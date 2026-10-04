import unittest
import runpy
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from common import make_job

from app.core.config import settings, Settings, BACKEND_DIR
from app.services import ai_service
from app.services.crawler import PlaywrightJobCrawler as Crawler


class StartupTests(unittest.TestCase):
    def test_reload_preserves_windows_subprocess_support(self):
        cases = [("win32", "development", False), ("linux", "development", True),
                 ("linux", "production", False)]
        for platform, environment, reload_enabled in cases:
            with self.subTest(platform=platform, environment=environment), \
                    patch("sys.platform", platform), \
                    patch.object(settings, "ENVIRONMENT", environment), \
                    patch("uvicorn.run") as start:
                runpy.run_path(str(BACKEND_DIR / "main.py"), run_name="__main__")
                self.assertEqual(start.call_args.kwargs["reload"], reload_enabled)
                self.assertEqual(start.call_args.kwargs["workers"], 1)


class ParserTests(unittest.TestCase):
    def test_salary_requires_currency_unit(self):
        for text in ("3-5年经验", "2024-2026年", "年龄20-30岁"):
            with self.subTest(text=text):
                self.assertEqual(Crawler._extract_salary(text), "")
        self.assertEqual(Crawler._extract_salary("薪资8-12K"), "8-12K")
        self.assertEqual(Crawler._extract_salary("1.5-2万元/月"), "1.5-2万元/月")
        self.assertEqual(Crawler._extract_salary("薪资面议"), "面议")

    def test_source_url_checks_hostname(self):
        self.assertTrue(Crawler._is_source_url("https://jobs.zhaopin.com/1", "zhaopin.com"))
        for url in ("https://zhaopin.com.evil.example/", "https://evil.example/?zhaopin.com", "javascript:zhaopin.com"):
            self.assertFalse(Crawler._is_source_url(url, "zhaopin.com"))

    def test_skill_parser_does_not_extract_partial_names(self):
        skills = Crawler._extract_skills("JavaScript，MongoDB，GitHub，Python")
        self.assertIn("JavaScript", skills)
        for name in ("Java", "Go", "Git"):
            self.assertNotIn(name, skills)

    def test_relative_directories_resolve_from_backend(self):
        config = Settings(_env_file=None, DATA_DIR="./data", LOG_DIR="./logs")
        self.assertEqual(config.DATA_DIR, str(BACKEND_DIR / "data"))
        self.assertEqual(config.LOG_DIR, str(BACKEND_DIR / "logs"))


class CrawlerTests(unittest.IsolatedAsyncioTestCase):
    async def test_search_keyword_is_encoded_and_foreign_links_are_ignored(self):
        page = MagicMock()
        page.content = AsyncMock(return_value='''<table>
            <tr><td><a href="https://evil.example/?zhaopin.com">外站职位_公司</a></td></tr>
            <tr><td>薪资30K</td></tr>
            <tr><td><a href="https://jobs.zhaopin.com/1">Python开发_测试公司 - 智联招聘</a></td></tr>
            <tr><td>南京，薪资8-12K，熟悉Python</td></tr></table>''')
        navigation = AsyncMock(return_value=True)
        with patch.object(Crawler, "_navigate_with_retry", navigation):
            jobs = await Crawler._crawl_ddg_lite(page, "C++ & SQL", "zhaopin.com", "智联招聘")
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].location, "南京")
        self.assertEqual(jobs[0].url, "https://jobs.zhaopin.com/1")
        self.assertIn("C%2B%2B+%26+SQL", navigation.call_args.args[1])

    async def test_failed_source_keeps_prior_results_and_closes_browser(self):
        playwright = MagicMock()
        playwright.__aenter__ = AsyncMock(return_value=playwright)
        playwright.__aexit__ = AsyncMock(return_value=False)
        browser = MagicMock()
        browser.close = AsyncMock()
        contexts = [MagicMock() for _ in range(4)]
        for context in contexts:
            context.new_page = AsyncMock(return_value=MagicMock())
            context.close = AsyncMock()
        first = [make_job(1, title="同一岗位"), make_job(2, title="同一岗位", location="上海")]
        with patch("app.services.crawler.PLAYWRIGHT_AVAILABLE", True), \
                patch("app.services.crawler.async_playwright", return_value=playwright), \
                patch.object(Crawler, "_create_browser", AsyncMock(return_value=browser)), \
                patch.object(Crawler, "_create_context", AsyncMock(side_effect=contexts)), \
                patch.object(Crawler, "_crawl_ddg_lite", AsyncMock(side_effect=[first, RuntimeError("来源失败"), []])), \
                patch.object(Crawler, "_crawl_bing", AsyncMock(return_value=[])), \
                patch("app.services.crawler.HumanBehaviorSimulator.random_delay", AsyncMock()):
            jobs = await Crawler.crawl("测试")
        self.assertEqual(len(jobs), 2)
        browser.close.assert_awaited_once()
        for context in contexts:
            context.close.assert_awaited_once()


class AIServiceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.old_log = list(ai_service._call_log)
        ai_service._call_log.clear()
        self.addCleanup(self.restore_log)

    def restore_log(self):
        ai_service._call_log[:] = self.old_log

    async def test_provider_defaults_follow_provider(self):
        with patch.object(settings, "AI_PROVIDER", "dashscope"), patch.object(settings, "AI_API_BASE_URL", None), patch.object(settings, "AI_MODEL", None):
            config = ai_service.get_provider_config()
        self.assertIn("dashscope", config["base_url"])
        self.assertEqual(config["model"], "qwen-turbo")

    async def test_placeholder_key_does_not_make_external_request(self):
        with patch.object(settings, "AI_API_KEY", "your_production_api_key_here"), patch.object(ai_service, "AsyncOpenAI") as factory:
            result = await ai_service.chat_completion("解析JD")
            health = await ai_service.health_check()
        factory.assert_not_called()
        self.assertTrue(result["is_fallback"])
        self.assertEqual(health["api_status"], "not_configured")
        self.assertEqual(len(ai_service.get_call_log()), 1)

    async def test_async_request_uses_configured_timeout(self):
        client = MagicMock()
        client.__aenter__ = AsyncMock(return_value=client)
        client.__aexit__ = AsyncMock(return_value=False)
        client.chat.completions.create = AsyncMock(return_value=SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="测试结果"))]))
        with patch.object(settings, "AI_API_KEY", "test-key"), patch.object(settings, "AI_TIMEOUT", 7), patch.object(ai_service, "AsyncOpenAI", return_value=client) as factory:
            result = await ai_service.chat_completion("测试请求")
        client.chat.completions.create.assert_awaited_once()
        self.assertEqual(factory.call_args.kwargs["timeout"], 7)
        self.assertFalse(result["is_fallback"])
        self.assertEqual(result["content"], "测试结果")

    async def test_failed_request_records_one_fallback_log(self):
        with patch.object(settings, "AI_API_KEY", "test-key"), patch.object(ai_service, "AsyncOpenAI", side_effect=RuntimeError("连接失败")):
            result = await ai_service.chat_completion("测试请求")
        self.assertTrue(result["is_fallback"])
        logs = ai_service.get_call_log()
        self.assertEqual(len(logs), 1)
        self.assertIn("连接失败", logs[0]["error_message"])
