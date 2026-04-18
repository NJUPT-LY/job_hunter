import json
import os
import uuid
from typing import Optional, List
from datetime import datetime
from app.models.schemas import Job
from app.core.config import settings


class JobService:
    data_file = os.path.join(settings.DATA_DIR, "jobs.json")
    
    @classmethod
    def _ensure_data_dir(cls):
        os.makedirs(settings.DATA_DIR, exist_ok=True)
        if not os.path.exists(cls.data_file):
            with open(cls.data_file, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False)
    
    @classmethod
    def _load_jobs(cls) -> List[Job]:
        cls._ensure_data_dir()
        with open(cls.data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return [Job(**job) for job in data]
    
    @classmethod
    def _save_jobs(cls, jobs: List[Job]):
        cls._ensure_data_dir()
        with open(cls.data_file, 'w', encoding='utf-8') as f:
            json.dump([job.dict() for job in jobs], f, ensure_ascii=False)
    
    @classmethod
    def list_jobs(cls, keyword: Optional[str] = None, location: Optional[str] = None, 
                  page: int = 1, page_size: int = 20) -> List[Job]:
        jobs = cls._load_jobs()
        
        if keyword:
            jobs = [j for j in jobs if keyword.lower() in j.title.lower() or 
                    keyword.lower() in j.description.lower()]
        
        if location:
            jobs = [j for j in jobs if location in j.location]
        
        start = (page - 1) * page_size
        end = start + page_size
        return jobs[start:end]
    
    @classmethod
    def search_jobs(cls, keyword: str) -> List[Job]:
        return cls.list_jobs(keyword=keyword, page_size=50)
    
    @classmethod
    def get_job(cls, job_id: str) -> Optional[Job]:
        jobs = cls._load_jobs()
        for job in jobs:
            if job.id == job_id:
                return job
        return None
    
    @classmethod
    async def crawl_jobs(cls, keyword: str) -> dict:
        from app.services.crawler import JobCrawler
        jobs = await JobCrawler.crawl(keyword)
        
        existing_jobs = cls._load_jobs()
        existing_urls = {j.url for j in existing_jobs if j.url}
        
        new_count = 0
        for job in jobs:
            if job.url and job.url not in existing_urls:
                existing_jobs.append(job)
                new_count += 1
        
        cls._save_jobs(existing_jobs)
        return {"message": f"爬取完成，新增{new_count}个职位", "total": len(existing_jobs), "new": new_count}
    
    @classmethod
    def add_sample_jobs(cls):
        cls._ensure_data_dir()
        jobs = cls._load_jobs()
        if jobs:
            return
        
        sample_jobs = [
            Job(
                id="1",
                title="前端开发工程师",
                company="某互联网公司",
                location="北京",
                salary="15-25K",
                experience="1-3年",
                education="本科",
                description="负责公司Web产品的前端开发，参与产品需求讨论，优化用户体验",
                requirements=["熟练掌握HTML/CSS/JavaScript", "熟悉React或Vue框架", "了解响应式设计"],
                skills=["HTML", "CSS", "JavaScript", "React", "Vue"],
                source="示例数据",
                crawl_time=datetime.now().isoformat()
            ),
            Job(
                id="2",
                title="Python后端开发工程师",
                company="某科技公司",
                location="上海",
                salary="18-30K",
                experience="1-3年",
                education="本科",
                description="负责公司后端服务开发，参与系统架构设计，优化系统性能",
                requirements=["熟练掌握Python", "熟悉Django或FastAPI框架", "了解MySQL/Redis等数据库"],
                skills=["Python", "Django", "FastAPI", "MySQL", "Redis"],
                source="示例数据",
                crawl_time=datetime.now().isoformat()
            ),
            Job(
                id="3",
                title="数据分析师",
                company="某金融公司",
                location="深圳",
                salary="12-20K",
                experience="不限",
                education="本科",
                description="负责业务数据分析，输出数据报告，为决策提供支持",
                requirements=["熟练使用SQL", "熟悉Python数据分析库", "具备良好的统计学基础"],
                skills=["SQL", "Python", "Pandas", "Excel", "Tableau"],
                source="示例数据",
                crawl_time=datetime.now().isoformat()
            ),
            Job(
                id="4",
                title="产品经理",
                company="某电商平台",
                location="杭州",
                salary="15-25K",
                experience="1-3年",
                education="本科",
                description="负责产品规划和设计，协调研发、设计团队，推进产品迭代",
                requirements=["具备产品思维", "熟练使用Axure/Figma", "良好的沟通协调能力"],
                skills=["产品规划", "Axure", "Figma", "数据分析", "项目管理"],
                source="示例数据",
                crawl_time=datetime.now().isoformat()
            ),
            Job(
                id="5",
                title="Java开发工程师",
                company="某银行科技部门",
                location="北京",
                salary="16-28K",
                experience="1-3年",
                education="本科",
                description="负责银行系统后端开发，参与系统设计和优化",
                requirements=["熟练掌握Java", "熟悉Spring生态", "了解分布式系统"],
                skills=["Java", "Spring Boot", "MySQL", "Redis", "微服务"],
                source="示例数据",
                crawl_time=datetime.now().isoformat()
            )
        ]
        
        cls._save_jobs(sample_jobs)
