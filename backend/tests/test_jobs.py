import asyncio
import json
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import AsyncMock, patch

from common import FileFixture, make_job
from app.services.job_service import JobService


class JobStorageTests(FileFixture, unittest.TestCase):
    def test_initial_data_file_is_created_in_its_parent(self):
        self.assertEqual(JobService.list_jobs(), [])
        self.assertTrue(self.data_path.exists())

    def test_concurrent_imports_do_not_lose_jobs(self):
        def import_one(index):
            return JobService.import_jobs([make_job(index).model_dump()])
        with ThreadPoolExecutor(max_workers=8) as executor:
            results = list(executor.map(import_one, range(40)))
        self.assertEqual(sum(result["new_imported"] for result in results), 40)
        self.assertEqual(len(JobService._load_jobs()), 40)
        self.assertEqual(len(json.loads(self.data_path.read_text(encoding="utf-8"))), 40)

    def test_failed_atomic_replace_preserves_data_and_cache(self):
        JobService._save_jobs([make_job(1)])
        original = self.data_path.read_bytes()
        with patch("app.services.job_service.os.replace", side_effect=OSError("磁盘写入失败")):
            with self.assertRaises(OSError):
                JobService.import_jobs([make_job(2).model_dump()])
        self.assertEqual(self.data_path.read_bytes(), original)
        self.assertEqual([job.id for job in JobService._load_jobs()], ["1"])
        self.assertEqual(list(self.data_path.parent.glob(".jobs-*.tmp")), [])

    def test_caller_cannot_mutate_cached_objects(self):
        JobService._save_jobs([make_job()])
        result = JobService._load_jobs()
        result[0].skills.append("虚构技能")
        result.append(make_job(2))
        self.assertEqual(len(JobService._load_jobs()), 1)
        self.assertNotIn("虚构技能", JobService.get_job("1").skills)

    def test_external_file_change_invalidates_cache(self):
        JobService._save_jobs([make_job()])
        self.data_path.write_text(json.dumps([make_job(1234).model_dump()]), encoding="utf-8")
        self.assertEqual(JobService._load_jobs()[0].id, "1234")

    def test_corrupt_file_is_not_overwritten_by_import(self):
        self.data_path.parent.mkdir(parents=True)
        self.data_path.write_text("broken json", encoding="utf-8")
        with self.assertRaises(IOError):
            JobService.import_jobs([make_job().model_dump()])
        self.assertEqual(self.data_path.read_text(encoding="utf-8"), "broken json")

    def test_dedup_checks_content_id_and_url(self):
        original = make_job(url="https://jobs.example.com/1")
        candidates = [make_job(2, title=original.title), make_job(1, title="不同职位"),
                      make_job(3, url=original.url), make_job(4, location="上海"),
                      make_job(5, title="独立岗位")]
        kept, duplicates, count = JobService.deduplicate_jobs(candidates, [original])
        self.assertEqual([job.id for job in kept], ["4", "5"])
        self.assertEqual((duplicates, count), (3, 2))

    def test_dedup_key_does_not_collide_with_separator_in_title(self):
        first = make_job(title="开发|测试", company="公司")
        second = make_job(2, title="开发", company="测试|公司")
        self.assertNotEqual(JobService.generate_dedup_key(first), JobService.generate_dedup_key(second))

    def test_import_reports_invalid_records_and_same_batch_duplicates(self):
        data = make_job().model_dump()
        result = JobService.import_jobs([data, data, {"title": "不完整"}, None])
        self.assertEqual(result["new_imported"], 1)
        self.assertEqual(result["duplicates_skipped"], 1)
        self.assertEqual(result["invalid_count"], 2)

    def test_search_and_export_use_same_filters(self):
        JobService._save_jobs([make_job(1, company="特殊公司"), make_job(2, location="上海")])
        page = JobService.list_jobs_page(" 特殊公司 ", "南京", 1, 1)
        self.assertEqual(page["total"], 1)
        self.assertEqual(page["items"][0].id, "1")
        self.assertEqual(JobService.export_jobs("特殊公司", "南京")["total"], 1)
        self.assertEqual(JobService.list_jobs_page(page=3, page_size=1)["items"], [])

    def test_legacy_generated_jobs_are_labelled_as_examples(self):
        JobService._save_jobs([make_job(source="AI实时获取", url="https://example.com/fake")])
        JobService._refresh_cache()
        job = JobService.get_job("1")
        self.assertEqual(job.source, "模型生成示例")
        self.assertIsNone(job.url)

    def test_sample_initializer_preserves_existing_data(self):
        JobService._save_jobs([make_job(99)])
        JobService.add_sample_jobs()
        self.assertEqual([job.id for job in JobService._load_jobs()], ["99"])

    def test_import_allows_undisclosed_salary(self):
        data = make_job().model_dump()
        data.pop("salary")
        result = JobService.import_jobs([data])
        self.assertEqual(result["new_imported"], 1)
        self.assertEqual(JobService.get_job("1").salary, "面议")


class CrawlServiceTests(FileFixture, unittest.IsolatedAsyncioTestCase):
    async def test_crawl_only_imports_actual_crawler_results(self):
        fetched = [make_job(1, salary=None, source="智联招聘"), make_job(2, title="Python开发1")]
        with patch("app.services.crawler.JobCrawler.crawl", AsyncMock(return_value=fetched)):
            result = await JobService.crawl_jobs("Python")
        self.assertEqual(result["new"], 1)
        self.assertEqual(result["fetched"], 2)
        self.assertEqual(JobService.get_job("1").salary, "面议")
        self.assertEqual(JobService.get_job("1").source, "智联招聘")

    async def test_empty_crawl_preserves_existing_jobs_and_reports_no_results(self):
        JobService._save_jobs([make_job(99)])
        with patch("app.services.crawler.JobCrawler.crawl", AsyncMock(return_value=[])):
            result = await JobService.crawl_jobs("Python")
        self.assertEqual((result["total"], result["new"], result["source"]), (1, 0, "无"))
        self.assertIn("未获取到", result["message"])
