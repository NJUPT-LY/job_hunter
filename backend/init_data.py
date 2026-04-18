import sys
sys.path.insert(0, '.')

from app.services.job_service import JobService

JobService.add_sample_jobs()
print("示例数据已生成!")
