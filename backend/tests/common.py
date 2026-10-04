import tempfile
from pathlib import Path
from unittest.mock import patch

from app.models.schemas import Job
from app.services.job_service import JobService


def make_job(index=1, **overrides):
    data = dict(id=str(index), title=f"Python开发{index}", company="测试公司",
                location="南京", salary="15-25K", description="负责后端开发",
                requirements=["精通Python"], skills=["Python", "SQL"], source="测试数据")
    data.update(overrides)
    return Job(**data)


class FileFixture:
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.data_path = Path(directory.name) / "storage" / "jobs.json"
        for name, value in (("data_file", str(self.data_path)), ("_cache", None),
                            ("_cache_path", None), ("_cache_stamp", None)):
            patcher = patch.object(JobService, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
