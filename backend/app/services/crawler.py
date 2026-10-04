"""
招聘网站爬虫 - Playwright 版本
使用 Playwright 模拟真实浏览器行为进行职位爬取
支持随机滚动、鼠标移动、随机停留等人类行为模拟
"""
from __future__ import annotations

import asyncio
import random
import re
import uuid
import logging
from typing import List, Optional, TYPE_CHECKING
from datetime import datetime
from urllib.parse import unquote, quote_plus, urlparse

from app.models.schemas import Job
from app.utils.skill_matching import contains_skill

if TYPE_CHECKING:
    from playwright.async_api import Page, Browser, BrowserContext

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    async_playwright = None  # type: ignore

logger = logging.getLogger(__name__)

# ============================================
# 请求头随机化配置
# ============================================
USER_AGENTS = [
    # Chrome on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    # Chrome on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    # Edge on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    # Chrome on Android (mobile-like but desktop-ish)
    "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
]

ACCEPT_LANGUAGES = [
    "zh-CN,zh;q=0.9,en;q=0.8",
    "zh-CN,zh;q=0.9",
    "zh,zh-CN;q=0.9,en;q=0.8,en-US;q=0.7",
    "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
]

VIEWPORTS = [
    {"width": 1920, "height": 1080},
    {"width": 1366, "height": 768},
    {"width": 1536, "height": 864},
    {"width": 1440, "height": 900},
    {"width": 1280, "height": 720},
]


class HumanBehaviorSimulator:
    """模拟人类浏览器行为"""

    @staticmethod
    async def random_delay(min_seconds: float = 2.0, max_seconds: float = 5.0):
        """随机停留时间，模拟人类阅读行为"""
        delay = random.uniform(min_seconds, max_seconds)
        logger.debug(f"随机停留 {delay:.2f} 秒")
        await asyncio.sleep(delay)

    @staticmethod
    async def random_scroll(page: Page, min_scrolls: int = 3, max_scrolls: int = 8):
        """随机页面滚动，多次，每次随机距离"""
        num_scrolls = random.randint(min_scrolls, max_scrolls)
        logger.debug(f"模拟随机滚动 {num_scrolls} 次")

        for i in range(num_scrolls):
            # 随机滚动距离 (100-800px)
            scroll_amount = random.randint(100, 800)
            # 随机选择滚动方向 (正数=向下，负数=向上偶尔)
            if random.random() < 0.85:  # 85%概率向下滚动
                scroll_amount = abs(scroll_amount)
            else:
                scroll_amount = -abs(scroll_amount)

            await page.evaluate(f"window.scrollBy(0, {scroll_amount})")
            # 每次滚动间短暂停留
            await asyncio.sleep(random.uniform(0.3, 1.2))

        # 偶尔滚动回顶部
        if random.random() < 0.3:
            await page.evaluate("window.scrollTo({top: 0, behavior: 'smooth'})")
            await asyncio.sleep(random.uniform(0.5, 1.5))

    @staticmethod
    async def random_mouse_movement(page: Page, num_moves: int = 5):
        """随机鼠标移动，模拟人类浏览行为"""
        logger.debug(f"模拟随机鼠标移动 {num_moves} 次")

        for _ in range(num_moves):
            x = random.randint(100, 1200)
            y = random.randint(100, 800)

            # 使用JavaScript模拟鼠标移动
            await page.mouse.move(x, y)
            await asyncio.sleep(random.uniform(0.1, 0.5))

    @staticmethod
    async def simulate_reading(page: Page):
        """模拟人类阅读行为：随机停留 + 轻微滚动 + 鼠标移动"""
        # 先随机停留
        await HumanBehaviorSimulator.random_delay(1.0, 3.0)

        # 随机小幅度滚动
        small_scroll = random.randint(50, 300)
        await page.evaluate(f"window.scrollBy(0, {small_scroll})")
        await asyncio.sleep(random.uniform(0.2, 0.8))

        # 随机鼠标移动
        await HumanBehaviorSimulator.random_mouse_movement(page, num_moves=3)

        # 再停留
        await HumanBehaviorSimulator.random_delay(1.0, 2.0)


class PlaywrightJobCrawler:
    """
    使用 Playwright 的招聘网站爬虫
    多数据源策略：
    1. 主数据源：通过 DuckDuckGo Lite 搜索引擎聚合招聘网站结果
    2. 备用数据源：通过 Bing 搜索聚合
    所有数据均来自真实招聘网站，无模拟数据
    """

    MAX_RETRIES = 3
    RETRY_DELAY = 2
    REQUEST_DELAY = (2.0, 5.0)  # 每个网站爬取后延迟2-5秒

    CITIES = [
        "北京", "上海", "广州", "深圳", "杭州", "成都", "南京", "武汉",
        "天津", "重庆", "苏州", "西安", "长沙", "郑州", "青岛", "大连",
        "厦门", "合肥", "济南", "福州", "昆明", "哈尔滨", "沈阳", "东莞",
        "佛山", "无锡", "宁波", "珠海", "温州", "贵阳", "南昌", "南宁",
        "石家庄", "长春", "太原", "呼和浩特", "兰州", "银川", "乌鲁木齐",
    ]

    COMMON_SKILLS = [
        "Python", "Java", "JavaScript", "TypeScript", "HTML5", "HTML", "CSS3", "CSS",
        "React", "Vue", "Vue.js", "Angular", "Node.js", "Django", "Flask", "FastAPI",
        "Spring", "Spring Boot", "MySQL", "PostgreSQL", "Redis", "MongoDB", "Oracle",
        "Docker", "Kubernetes", "Linux", "Git", "AWS", "Azure",
        "算法", "数据结构", "微服务", "分布式", "机器学习", "深度学习",
        "数据分析", "SQL", "Pandas", "NumPy", "Tableau", "Figma", "Axure",
        "TCP/IP", "HTTP", "RESTful", "GraphQL", "WebSocket",
        "Go", "Golang", "C++", "C#", ".NET", "PHP", "Swift",
        "Kotlin", "Flutter", "小程序",
        "Jenkins", "CI/CD", "Nginx", "Kafka", "RabbitMQ",
        "PyTorch", "TensorFlow", "NLP", "推荐系统",
        "产品规划", "用户体验", "用户研究", "需求分析",
        "项目管理", "沟通协调", "团队协作",
    ]

    @classmethod
    def _get_random_headers(cls) -> dict:
        """获取随机请求头"""
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": random.choice(ACCEPT_LANGUAGES),
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
        }

    @classmethod
    async def _create_browser(cls, playwright) -> Browser:
        """创建浏览器实例"""
        browser = await playwright.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-extensions",
                "--disable-infobars",
                "--disable-notifications",
                "--lang=zh-CN",
            ],
        )
        return browser

    @classmethod
    async def _create_context(cls, browser: Browser) -> BrowserContext:
        """创建浏览器上下文，配置随机化"""
        viewport = random.choice(VIEWPORTS)
        context = await browser.new_context(
            viewport=viewport,
            user_agent=random.choice(USER_AGENTS),
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
            java_script_enabled=True,
        )
        # 设置额外的请求头
        extra_headers = cls._get_random_headers()
        await context.set_extra_http_headers(extra_headers)

        # 注入脚本隐藏 webdriver 痕迹
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            // 覆盖 chrome.runtime
            window.chrome = {
                runtime: {}
            };
            // 覆盖 permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)
        return context

    @classmethod
    async def _simulate_human_behavior(cls, page: Page):
        """在页面上模拟人类行为"""
        behavior = HumanBehaviorSimulator()

        # 页面加载后模拟阅读行为
        await behavior.simulate_reading(page)

        # 随机滚动
        await behavior.random_scroll(page, min_scrolls=3, max_scrolls=8)

        # 随机鼠标移动
        await behavior.random_mouse_movement(page, num_moves=5)

        # 再次阅读
        await behavior.simulate_reading(page)

    @classmethod
    async def _navigate_with_retry(cls, page: Page, url: str, timeout: int = 30000) -> bool:
        """带重试的页面导航"""
        for attempt in range(cls.MAX_RETRIES):
            try:
                logger.debug(f"导航到 {url[:80]}... 尝试 {attempt+1}/{cls.MAX_RETRIES}")
                response = await page.goto(url, wait_until="domcontentloaded", timeout=timeout)

                if response and response.status == 200:
                    # 等待页面完全加载
                    await page.wait_for_load_state("domcontentloaded", timeout=15000)
                    # 模拟人类行为
                    await cls._simulate_human_behavior(page)
                    return True
                else:
                    status = response.status if response else "unknown"
                    logger.warning(f"页面加载状态码: {status}, 尝试 {attempt+1}/{cls.MAX_RETRIES}")

            except Exception as e:
                logger.warning(f"页面导航失败: {e}, 尝试 {attempt+1}/{cls.MAX_RETRIES}")

            if attempt < cls.MAX_RETRIES - 1:
                delay = cls.RETRY_DELAY * (attempt + 1) + random.uniform(0, 1)
                logger.debug(f"等待 {delay:.2f} 秒后重试")
                await asyncio.sleep(delay)

        return False

    @classmethod
    async def crawl(cls, keyword: str, max_pages: int = 4) -> List[Job]:
        if not PLAYWRIGHT_AVAILABLE:
            logger.warning("Playwright 未安装，无法使用爬虫功能")
            return []
        keyword = keyword.strip()
        if not keyword or max_pages < 1:
            return []
        jobs = []
        try:
            async with async_playwright() as playwright:
                browser = await cls._create_browser(playwright)
                try:
                    sources = [("zhaopin.com", "智联招聘", 10),
                               ("51job.com", "前程无忧", 5),
                               ("lagou.com", "拉勾网", 3), (None, "Bing", 3)]
                    for site, name, threshold in sources[:max_pages]:
                        if len(jobs) >= threshold:
                            continue
                        context = await cls._create_context(browser)
                        try:
                            page = await context.new_page()
                            if site:
                                jobs.extend(await cls._crawl_ddg_lite(page, keyword, site, name))
                            else:
                                jobs.extend(await cls._crawl_bing(page, keyword))
                        except Exception as exc:
                            logger.warning("%s 获取失败: %s", name, exc)
                        finally:
                            await context.close()
                        await HumanBehaviorSimulator.random_delay(*cls.REQUEST_DELAY)
                finally:
                    await browser.close()
        except Exception as exc:
            logger.error("招聘数据获取异常: %s", exc)
        # 某个来源失败时保留其他来源的结果，同岗位在不同城市分别保留。
        seen = set()
        unique_jobs = []
        for job in jobs:
            key = (job.title.strip().casefold(), job.company.strip().casefold(),
                   job.location.strip().casefold())
            if key not in seen:
                seen.add(key)
                job.title = job.title[:100]
                job.company = job.company[:50]
                unique_jobs.append(job)
        return unique_jobs

    @classmethod
    async def _crawl_ddg_lite(cls, page: Page, keyword: str, site: str, source_name: str) -> List[Job]:
        """
        通过 DuckDuckGo Lite 搜索聚合职位
        DDG Lite 是轻量级 HTML 版本，更容易抓取
        """
        jobs = []

        # 先访问 DDG 主页获取必要 cookie
        try:
            await page.goto("https://lite.duckduckgo.com/lite/", wait_until="domcontentloaded", timeout=10000)
        except Exception:
            try:
                await page.goto("https://duckduckgo.com/", wait_until="domcontentloaded", timeout=10000)
            except Exception:
                pass

        query = f"site:{site} {keyword}"
        search_url = f"https://lite.duckduckgo.com/lite/?q={quote_plus(query)}"

        success = await cls._navigate_with_retry(page, search_url)
        if not success:
            logger.warning(f"DDG Lite 无响应: query={query}")
            return jobs

        try:
            content = await page.content()
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(content, "html.parser")

            # DDG Lite 结果在 table 的行中
            # 格式: 标题行(带链接) + 摘要行
            rows = soup.select("tr")

            for i, row in enumerate(rows):
                a_elem = row.select_one("a")
                if not a_elem:
                    continue

                title = a_elem.get_text(strip=True)
                raw_url = a_elem.get("href", "")

                if not title or len(title) < 5:
                    continue

                # 提取真实URL
                real_url = cls._extract_real_url(raw_url)
                if not cls._is_source_url(real_url, site):
                    continue

                # 获取下一行的摘要
                snippet = ""
                next_row = row.find_next_sibling("tr")
                if next_row:
                    td = next_row.select_one("td")
                    if td:
                        snippet = td.get_text(strip=True)

                # 解析标题
                parsed = cls._parse_title(title)
                if not parsed:
                    continue

                # 补充信息
                location = parsed["location"] or cls._extract_location(snippet)
                salary = parsed["salary"] or cls._extract_salary(snippet)
                skills = cls._extract_skills(title + " " + snippet)

                jobs.append(Job(
                    id=str(uuid.uuid4()),
                    title=parsed["title"],
                    company=parsed["company"],
                    location=location or "不限",
                    salary=salary or "面议",
                    experience=parsed.get("experience", ""),
                    education=parsed.get("education", ""),
                    description=snippet if snippet else "暂无详细描述",
                    requirements=cls._extract_requirements(snippet),
                    skills=skills,
                    source=source_name,
                    crawl_time=datetime.now().isoformat(),
                    url=real_url
                ))

                if len(jobs) >= 10:
                    break

        except Exception as e:
            logger.error(f"解析DDG Lite页面失败: {e}")

        return jobs

    @classmethod
    async def _crawl_bing(cls, page: Page, keyword: str) -> List[Job]:
        """通过 Bing 搜索聚合职位（兜底方案）"""
        jobs = []

        # 先访问 Bing 主页获取 cookie
        try:
            await page.goto("https://www.bing.com/?cc=cn", wait_until="domcontentloaded", timeout=10000)
        except Exception:
            pass

        query = f"site:zhaopin.com {keyword} 招聘"
        search_url = f"https://www.bing.com/search?q={quote_plus(query)}&cc=cn&setlang=zh-CN"

        success = await cls._navigate_with_retry(page, search_url)
        if not success:
            return jobs

        try:
            content = await page.content()
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(content, "html.parser")

            # Bing 搜索结果
            results = soup.select("li.b_algo")

            for result in results:
                title_elem = result.select_one("h2 a")
                if not title_elem:
                    continue

                title = title_elem.get_text(strip=True)
                url = title_elem.get("href", "").strip()

                snippet_elem = result.select_one("p")
                snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

                if not any(cls._is_source_url(url, site) for site in ("zhaopin.com", "51job.com")):
                    continue

                source = "智联招聘" if "zhaopin.com" in url else "前程无忧"

                parsed = cls._parse_title(title)
                if not parsed:
                    continue

                location = parsed["location"] or cls._extract_location(snippet)
                salary = parsed["salary"] or cls._extract_salary(snippet)
                skills = cls._extract_skills(title + " " + snippet)

                jobs.append(Job(
                    id=str(uuid.uuid4()),
                    title=parsed["title"],
                    company=parsed["company"],
                    location=location or "不限",
                    salary=salary or "面议",
                    experience=parsed.get("experience", ""),
                    education=parsed.get("education", ""),
                    description=snippet if snippet else "暂无详细描述",
                    requirements=cls._extract_requirements(snippet),
                    skills=skills,
                    source=source,
                    crawl_time=datetime.now().isoformat(),
                    url=url
                ))

                if len(jobs) >= 10:
                    break

        except Exception as e:
            logger.error(f"解析Bing页面失败: {e}")

        return jobs

    @classmethod
    def _extract_real_url(cls, raw_url: str) -> str:
        """从跳转URL中提取真实URL"""
        if "uddg=" in raw_url:
            match = re.search(r'uddg=([^&]+)', raw_url)
            if match:
                return unquote(match.group(1))
        return raw_url

    @staticmethod
    def _is_source_url(url: str, site: str) -> bool:
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
        return parsed.scheme in ("http", "https") and (host == site or host.endswith("." + site))

    @classmethod
    def _parse_title(cls, raw_title: str) -> Optional[dict]:
        """解析搜索结果标题"""
        title = raw_title
        for suffix in [" - 智联招聘", " - 51job", " - 前程无忧", " - 拉勾网", " - BOSS直聘"]:
            if suffix in title:
                title = title.replace(suffix, "")
                break

        parts = title.split("_")
        job_title = ""
        company = ""

        if parts:
            job_title = parts[0].strip()

        if len(parts) >= 2:
            company_part = parts[1].strip().replace("招聘", "").strip()
            company = company_part

        if not job_title:
            return None

        return {
            "title": job_title,
            "company": company or "未知公司",
            "location": cls._extract_location(raw_title),
            "salary": cls._extract_salary(raw_title),
            "experience": cls._extract_experience(raw_title),
            "education": cls._extract_education(raw_title),
        }

    @classmethod
    def _extract_location(cls, text: str) -> str:
        """提取地点信息"""
        if not text:
            return ""
        for city in cls.CITIES:
            if city in text:
                return city
        return ""

    @classmethod
    def _extract_salary(cls, text: str) -> str:
        """提取薪资信息"""
        if not text:
            return ""
        if "面议" in text:
            return "面议"
        # 必须存在薪资单位，不能把“3-5年经验”误当成薪资。
        match = re.search(
            r"\d+(?:\.\d+)?\s*[Kk万千元]?\s*[-~–至]\s*"
            r"\d+(?:\.\d+)?\s*(?:[Kk]|[万千]元?|元)(?:/[月年日])?(?:[·*]\d+薪)?",
            text,
        )
        return match.group(0).strip() if match else ""

    @classmethod
    def _extract_experience(cls, text: str) -> str:
        """提取经验要求"""
        if not text:
            return ""
        patterns = [
            r"(5-10年|3-5年|1-3年|10年以上)",
            r"(\d+-\d+年)",
            r"(\d+年以上)",
            r"(应届毕业生|应届生|在校)",
            r"(经验不限)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return ""

    @classmethod
    def _extract_education(cls, text: str) -> str:
        """提取学历要求"""
        if not text:
            return ""
        for edu in ["博士", "硕士", "本科", "大专"]:
            if edu in text:
                return edu
        return ""

    @classmethod
    def _extract_skills(cls, text: str) -> List[str]:
        """提取技能关键词"""
        if not text:
            return []
        found = []
        for skill in cls.COMMON_SKILLS:
            if contains_skill(text, skill):
                found.append(skill)
        return found[:15]

    @classmethod
    def _extract_requirements(cls, text: str) -> List[str]:
        """提取职位要求列表"""
        if not text:
            return []
        reqs = []
        edu = cls._extract_education(text)
        if edu:
            reqs.append(f"学历要求: {edu}")
        exp = cls._extract_experience(text)
        if exp:
            reqs.append(f"工作经验: {exp}")
        skills = cls._extract_skills(text)
        if skills:
            reqs.append(f"技能要求: {', '.join(skills[:5])}")
        return reqs


# 向后兼容别名
JobCrawler = PlaywrightJobCrawler
