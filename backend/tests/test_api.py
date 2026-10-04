import logging
import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from common import FileFixture, make_job
from app.core.config import settings
from app.main import create_app
from app.services.job_service import JobService


class ApiTests(FileFixture, unittest.TestCase):
    def setUp(self):
        super().setUp()
        old_disable = logging.root.manager.disable
        logging.disable(logging.CRITICAL)
        self.addCleanup(logging.disable, old_disable)
        patcher = patch.object(settings, "AI_API_KEY", None)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.client = TestClient(create_app())
        self.addCleanup(self.client.close)

    def test_pagination_returns_real_total_and_requested_page(self):
        JobService._save_jobs([make_job(index) for index in range(43)])
        response = self.client.get("/api/v1/jobs/page", params={"page": 3, "page_size": 20})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["total"], 43)
        self.assertEqual(len(response.json()["items"]), 3)
        self.assertEqual(response.json()["items"][0]["id"], "40")
        # 原有列表接口继续返回数组。
        self.assertIsInstance(self.client.get("/api/v1/jobs/").json(), list)

    def test_stats_reflect_stored_jobs(self):
        JobService._save_jobs([make_job(1), make_job(2, location="上海", skills=["python", "React"])])
        self.assertEqual(self.client.get("/api/v1/jobs/stats").json(),
                         {"total": 2, "cities": 2, "companies": 1, "skills": 3})

    def test_missing_job_and_skill_gap_return_404(self):
        self.assertEqual(self.client.get("/api/v1/jobs/missing").status_code, 404)
        response = self.client.post("/api/v1/analysis/gap", json={"job_id": "missing", "user_skills": {"skills": []}})
        self.assertEqual(response.status_code, 404)

    def test_blank_business_inputs_return_422(self):
        bodies = [('/jobs/crawl', {"keyword": " "}),
                  ('/analysis/parse-jd', {"jd_text": "\n"}),
                  ('/action-plan/generate', {"job_title": " "}),
                  ('/resume/evaluate', {"resume_content": " ", "target_job": "前端"}),
                  ('/resume/optimize', {"resume_content": "简历", "target_job": " "}),
                  ('/interview/evaluate', {"question": "问题", "answer": " ", "job_title": "前端"})]
        for path, body in bodies:
            with self.subTest(path=path):
                self.assertEqual(self.client.post('/api/v1' + path, json=body).status_code, 422)

    def test_invalid_skill_values_return_422(self):
        response = self.client.post("/api/v1/analysis/gap", json={"job_id": "1", "user_skills": {"skills": [None]}})
        self.assertEqual(response.status_code, 422)

    def test_model_fallback_endpoints_return_renderable_data(self):
        plan = self.client.post("/api/v1/action-plan/generate", json={"job_title": "数据工程师"})
        self.assertEqual(plan.status_code, 200)
        self.assertGreaterEqual(len(plan.json()), 3)
        evaluation = self.client.post("/api/v1/interview/evaluate", json={
            "question": "项目经验", "answer": "我参与一个Python项目，负责接口开发和测试。", "job_title": "后端"})
        self.assertEqual(evaluation.status_code, 200)
        self.assertTrue(evaluation.json()["is_fallback"])
        self.assertIsInstance(evaluation.json()["strengths"], list)
        jd = self.client.post("/api/v1/analysis/parse-jd", json={"jd_text": "本科，负责Python开发，3年经验"})
        self.assertEqual(jd.status_code, 200)
        self.assertEqual(jd.json()["required_skills"], ["Python"])

    def test_crawl_timeout_returns_504(self):
        import asyncio
        async def slow_crawl(keyword):
            await asyncio.sleep(10)
        with patch.object(settings, "CRAWL_TIMEOUT", 0.01), patch.object(JobService, "crawl_jobs", slow_crawl):
            response = self.client.post("/api/v1/jobs/crawl", json={"keyword": "Python"})
        self.assertEqual(response.status_code, 504)

    def test_interview_invalid_index_and_type_are_rejected(self):
        body = {"job_title": "前端", "interview_type": "技术面", "question_index": 999}
        self.assertEqual(self.client.post("/api/v1/interview/simulate", json=body).status_code, 400)
        body["question_index"] = -1
        self.assertEqual(self.client.post("/api/v1/interview/simulate", json=body).status_code, 422)
        self.assertEqual(self.client.get("/api/v1/interview/questions?difficulty=未知").status_code, 422)

    def test_readiness_returns_503_for_missing_data_directory(self):
        with patch.object(settings, "DATA_DIR", str(self.data_path.parent / "missing")):
            response = self.client.get("/ready")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["status"], "not_ready")

    def test_rate_limit_response_includes_cors_headers(self):
        with patch.object(settings, "RATE_LIMIT_MAX_REQUESTS", 1):
            client = TestClient(create_app())
        self.addCleanup(client.close)
        headers = {"Origin": "http://localhost:5173"}
        self.assertEqual(client.get("/api/v1/jobs/stats", headers=headers).status_code, 200)
        response = client.get("/api/v1/jobs/stats", headers=headers)
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.headers["access-control-allow-origin"], headers["Origin"])

    def test_custom_api_prefix_is_used(self):
        with patch.object(settings, "API_PREFIX", "/service"):
            client = TestClient(create_app())
        self.addCleanup(client.close)
        self.assertEqual(client.get("/service/jobs/stats").status_code, 200)
        self.assertEqual(client.get("/service/health/detailed").status_code, 200)
