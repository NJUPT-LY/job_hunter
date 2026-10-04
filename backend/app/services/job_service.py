import json
import os
import uuid
import threading
import tempfile
from pathlib import Path
import time
import logging
from typing import Optional, List, Tuple
from datetime import datetime
from app.models.schemas import Job
from app.core.config import settings

logger = logging.getLogger(__name__)


# 数据验证配置
REQUIRED_JOB_FIELDS = ['title', 'company', 'location']
OPTIONAL_JOB_FIELDS_WITH_DEFAULTS = {
    'salary': '面议',
    'description': '',
    'requirements': [],
    'skills': []
}
MAX_FIELD_LENGTHS = {
    'title': 200,
    'company': 100,
    'location': 100,
    'salary': 50
}


class CacheEntry:
    """缓存条目，包含数据和过期时间"""
    def __init__(self, data, ttl_seconds: int = 60):
        self.data = data
        self.expires_at = time.time() + ttl_seconds
        self.created_at = time.time()

    def is_expired(self) -> bool:
        return time.time() > self.expires_at


class JobService:
    """职位服务类，提供职位数据的CRUD操作，支持并发控制和缓存"""

    # 类级别的锁和缓存
    _lock = threading.RLock()
    _cache: Optional[CacheEntry] = None
    _cache_ttl = 60  # 缓存过期时间（秒）
    _cache_path = None
    _cache_stamp = None
    _max_retries = 3  # 最大重试次数
    _retry_delay = 0.1  # 重试延迟（秒）

    # 类级别属性
    data_file = os.path.join(settings.DATA_DIR, "jobs.json")

    @classmethod
    def validate_job_data(cls, job_data: dict) -> Tuple[bool, str]:
        """
        验证职位数据格式是否正确

        Args:
            job_data: 职位数据字典

        Returns:
            Tuple[bool, str]: (是否有效, 错误信息)
        """
        if not isinstance(job_data, dict):
            return False, "职位数据必须是对象"

        # 检查必填字段
        for field in REQUIRED_JOB_FIELDS:
            if field not in job_data or not job_data[field]:
                return False, f"缺少必填字段: {field}"
            if not isinstance(job_data[field], str):
                return False, f"字段 '{field}' 必须是字符串类型"
            if not job_data[field].strip():
                return False, f"字段 '{field}' 不能为空字符串"

        # 检查字段长度限制
        for field, max_len in MAX_FIELD_LENGTHS.items():
            if field in job_data and isinstance(job_data[field], str):
                if len(job_data[field]) > max_len:
                    return False, f"字段 '{field}' 长度超过限制({max_len}字符)"

        # 验证并设置可选字段默认值
        for field, default_value in OPTIONAL_JOB_FIELDS_WITH_DEFAULTS.items():
            if field not in job_data or job_data[field] is None:
                job_data[field] = default_value.copy() if isinstance(default_value, list) else default_value

        # 验证source字段
        if 'source' not in job_data or not job_data['source']:
            job_data['source'] = '未知来源'

        if not job_data['salary']:
            job_data['salary'] = '面议'
        if not isinstance(job_data['salary'], str):
            return False, "字段 'salary' 必须是字符串类型"

        # 验证salary格式（可选，但有值时需合理）
        salary = job_data.get('salary', '')
        if salary and not any(kw in salary for kw in ['K', 'k', '万', '元', '面议', '不限']):
            logger.warning(f"薪资格式可能不规范: {salary}")

        return True, "验证通过"

    @classmethod
    def create_validated_job(cls, job_data: dict, source: str = "未知来源") -> Optional[Job]:
        """
        创建经过验证的Job对象，自动补充缺失字段和ID

        Args:
            job_data: 职位数据字典
            source: 数据来源

        Returns:
            Optional[Job]: 验证通过的Job对象，验证失败返回None
        """
        # 复制数据避免修改原始数据
        if not isinstance(job_data, dict):
            return None
        data = job_data.copy()

        # 确保source字段
        if not data.get('source'):
            data['source'] = source
        if data['source'] == 'AI实时获取':
            data['source'] = '模型生成示例'
            data['url'] = None

        # 验证数据
        is_valid, error_msg = cls.validate_job_data(data)
        if not is_valid:
            logger.warning(f"职位数据验证失败: {error_msg}, 数据: {data.get('title', 'N/A')}")
            return None

        # 生成ID（如果没有）
        if not data.get('id'):
            data['id'] = str(uuid.uuid4())

        # 设置crawl_time（如果没有）
        if not data.get('crawl_time'):
            data['crawl_time'] = datetime.now().isoformat()

        try:
            return Job(**data)
        except Exception as e:
            logger.error(f"创建Job对象失败: {str(e)}")
            return None

    @classmethod
    def generate_dedup_key(cls, job: Job) -> tuple:
        """
        生成去重键：基于 title + company + location

        Args:
            job: Job对象

        Returns:
            tuple: 去重键（小写标准化）
        """
        title = job.title.strip().lower()
        company = job.company.strip().lower()
        location = job.location.strip().lower()
        return (title, company, location)

    @classmethod
    def deduplicate_jobs(cls, jobs: List[Job], existing_jobs: List[Job] = None) -> Tuple[List[Job], int, int]:
        """
        按职位内容、ID 和链接去重，保留先入库的数据

        去重规则：
        - 基于 title + company + location 组合去重
        - 同时检查 ID 和非空链接
        - 如果重复，保留第一条

        Args:
            jobs: 待去重的职位列表
            existing_jobs: 系统中已存在的职位列表（可选）

        Returns:
            Tuple[List[Job], int, int]: (去重后的新职位列表, 去重数量, 保留总数)
        """
        if not jobs:
            return [], 0, 0

        # 如果有现有职位，先建立已存在的去重键集合
        existing_dedup_keys = set()
        if existing_jobs:
            for job in existing_jobs:
                existing_dedup_keys.add(cls.generate_dedup_key(job))

        existing_ids = {job.id for job in existing_jobs or []}
        existing_urls = {job.url for job in existing_jobs or [] if job.url}
        sorted_jobs = jobs

        # 去重处理
        deduplicated = []
        seen_keys = set()
        duplicate_count = 0

        for job in sorted_jobs:
            dedup_key = cls.generate_dedup_key(job)

            # 检查是否与现有数据重复
            if (dedup_key in existing_dedup_keys or job.id in existing_ids
                    or (job.url and job.url in existing_urls)):
                duplicate_count += 1
                continue

            # 检查是否与本次数据中的已保留数据重复
            if dedup_key in seen_keys:
                duplicate_count += 1
                continue

            seen_keys.add(dedup_key)
            existing_ids.add(job.id)
            if job.url:
                existing_urls.add(job.url)
            deduplicated.append(job)

        return deduplicated, duplicate_count, len(deduplicated)

    @classmethod
    def _ensure_data_dir(cls):
        path = Path(cls.data_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        with cls._lock:
            if not path.exists():
                path.write_text("[]", encoding="utf-8")

    @classmethod
    def _file_stamp(cls):
        stat = Path(cls.data_file).stat()
        return (stat.st_mtime_ns, stat.st_size)

    @classmethod
    def _load_jobs_from_file(cls, max_retries: int = None) -> List[Job]:
        retries = max_retries or cls._max_retries
        cls._ensure_data_dir()
        for attempt in range(retries):
            try:
                with cls._lock:
                    data = json.loads(Path(cls.data_file).read_text(encoding="utf-8"))
                    if not isinstance(data, list):
                        raise ValueError("职位数据文件必须是数组")
                    jobs = [Job.model_validate(item) for item in data]
                    # 旧版本把模型编造的岗位标成实时招聘，读取时纠正来源。
                    for job in jobs:
                        if job.source == "AI实时获取":
                            job.source = "模型生成示例"
                            job.url = None
                    return jobs
            except (OSError, ValueError) as exc:
                if attempt + 1 == retries:
                    raise IOError("职位数据文件无法读取，请检查文件或恢复备份") from exc
                time.sleep(cls._retry_delay * (attempt + 1))

    @classmethod
    def _save_jobs_to_file(cls, jobs: List[Job], max_retries: int = None) -> None:
        cls._ensure_data_dir()
        # 同目录临时文件加原子替换，写入失败时保留原文件。
        with cls._lock:
            temporary_path = None
            try:
                with tempfile.NamedTemporaryFile(
                    mode="w", encoding="utf-8", dir=Path(cls.data_file).parent,
                    prefix=".jobs-", suffix=".tmp", delete=False,
                ) as file:
                    temporary_path = file.name
                    json.dump([job.model_dump() for job in jobs], file,
                              ensure_ascii=False, indent=2)
                    file.flush()
                    os.fsync(file.fileno())
                os.replace(temporary_path, cls.data_file)
            finally:
                if temporary_path and os.path.exists(temporary_path):
                    os.unlink(temporary_path)

    @classmethod
    def _load_jobs(cls) -> List[Job]:
        with cls._lock:
            cls._ensure_data_dir()
            stamp = cls._file_stamp()
            if (cls._cache is None or cls._cache.is_expired()
                    or cls._cache_path != cls.data_file or cls._cache_stamp != stamp):
                cls._cache = CacheEntry(cls._load_jobs_from_file(), cls._cache_ttl)
                cls._cache_path = cls.data_file
                cls._cache_stamp = stamp
            return [job.model_copy(deep=True) for job in cls._cache.data]

    @classmethod
    def _save_jobs(cls, jobs: List[Job]):
        with cls._lock:
            cls._save_jobs_to_file(jobs)
            cls._cache = CacheEntry([job.model_copy(deep=True) for job in jobs], cls._cache_ttl)
            cls._cache_path = cls.data_file
            cls._cache_stamp = cls._file_stamp()

    @classmethod
    def _refresh_cache(cls):
        with cls._lock:
            cls._cache = None

    @classmethod
    def _append_jobs(cls, jobs: List[Job]):
        # 读取、去重、写入属于同一事务，避免两个导入请求互相覆盖。
        with cls._lock:
            existing = cls._load_jobs()
            new_jobs, duplicates, _ = cls.deduplicate_jobs(jobs, existing)
            if new_jobs:
                cls._save_jobs(existing + new_jobs)
            return len(new_jobs), duplicates, len(existing) + len(new_jobs)

    @classmethod
    def _filter_jobs(cls, keyword: Optional[str] = None, location: Optional[str] = None):
        jobs = cls._load_jobs()
        keyword = (keyword or "").strip().casefold()
        location = (location or "").strip().casefold()
        if keyword:
            jobs = [job for job in jobs if keyword in " ".join(
                [job.title, job.company, job.description, *job.skills]).casefold()]
        if location:
            jobs = [job for job in jobs if location in job.location.casefold()]
        return jobs

    @classmethod
    def list_jobs_page(cls, keyword=None, location=None, page=1, page_size=20):
        jobs = cls._filter_jobs(keyword, location)
        start = (page - 1) * page_size
        return {"items": jobs[start:start + page_size], "total": len(jobs),
                "page": page, "page_size": page_size}

    @classmethod
    def get_stats(cls):
        jobs = cls._load_jobs()
        return {"total": len(jobs), "cities": len({job.location for job in jobs}),
                "companies": len({job.company for job in jobs}),
                "skills": len({skill.casefold() for job in jobs for skill in job.skills})}

    @classmethod
    def list_jobs(cls, keyword: Optional[str] = None, location: Optional[str] = None,
                  page: int = 1, page_size: int = 20) -> List[Job]:
        """
        获取职位列表，支持关键词和位置过滤，分页

        Args:
            keyword: 搜索关键词
            location: 工作地点
            page: 页码
            page_size: 每页数量

        Returns:
            List[Job]: 过滤并分页后的职位列表
        """
        jobs = cls._filter_jobs(keyword, location)

        start = (page - 1) * page_size
        end = start + page_size
        return jobs[start:end]

    @classmethod
    def search_jobs(cls, keyword: str) -> List[Job]:
        """
        搜索职位

        Args:
            keyword: 搜索关键词

        Returns:
            List[Job]: 搜索结果
        """
        return cls.list_jobs(keyword=keyword, page_size=50)

    @classmethod
    def get_job(cls, job_id: str) -> Optional[Job]:
        """
        获取单个职位详情

        Args:
            job_id: 职位ID

        Returns:
            Optional[Job]: 职位对象，不存在时返回None
        """
        jobs = cls._load_jobs()
        for job in jobs:
            if job.id == job_id:
                return job
        return None

    @classmethod
    async def crawl_jobs(cls, keyword: str) -> dict:
        from app.services.crawler import JobCrawler
        keyword = keyword.strip()
        if not keyword:
            raise ValueError("搜索关键词不能为空")
        # 招聘数据仅取自原始网页；模型生成的数据不能作为真实岗位入库。
        crawled = await JobCrawler.crawl(keyword)
        jobs = []
        for job in crawled:
            data = job.model_dump()
            data["salary"] = data.get("salary") or "面议"
            validated = cls.create_validated_job(data, source="爬虫获取")
            if validated:
                jobs.append(validated)
        new_count, duplicates, total = cls._append_jobs(jobs)
        message = (f"获取完成，新增{new_count}个职位" if jobs
                   else "未获取到职位，请检查网络、浏览器安装或更换关键词")
        return {"message": message, "total": total, "new": new_count,
                "source": "爬虫获取" if jobs else "无", "fetched": len(jobs),
                "dedup_stats": {"duplicates_removed": duplicates, "final_count": new_count}}

    @classmethod
    def add_sample_jobs(cls):
        """添加示例数据"""
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
            ),
            Job(
                id="6",
                title="前端架构师",
                company="某头部互联网公司",
                location="上海",
                salary="35-55K",
                experience="5-10年",
                education="本科",
                description="负责前端技术架构设计与演进，主导核心前端基础设施建设，推动团队技术能力提升",
                requirements=["8年以上前端开发经验", "深入理解React/Vue原理", "具备大型项目架构经验", "熟悉工程化工具链"],
                skills=["React", "Vue", "TypeScript", "Webpack", "Node.js", "微前端"],
                source="示例数据",
                crawl_time=datetime.now().isoformat()
            ),
            Job(
                id="7",
                title="机器学习工程师",
                company="某AI独角兽企业",
                location="北京",
                salary="25-45K",
                experience="3-5年",
                education="硕士",
                description="负责NLP/推荐算法模型的研发和上线，参与大规模分布式训练框架搭建",
                requirements=["精通Python", "熟悉PyTorch/TensorFlow", "有NLP或推荐系统经验", "发表论文或开源项目优先"],
                skills=["Python", "PyTorch", "NLP", "推荐系统", "分布式训练", "Docker"],
                source="示例数据",
                crawl_time=datetime.now().isoformat()
            ),
            Job(
                id="8",
                title="运维工程师",
                company="某云计算公司",
                location="深圳",
                salary="12-22K",
                experience="1-3年",
                education="本科",
                description="负责公司服务器运维、容器化管理和CI/CD流程建设，保障系统高可用",
                requirements=["熟悉Linux系统管理", "掌握Docker/K8s", "了解CI/CD工具链", "有监控报警系统搭建经验"],
                skills=["Linux", "Docker", "Kubernetes", "Jenkins", "Prometheus", "Ansible"],
                source="示例数据",
                crawl_time=datetime.now().isoformat()
            ),
            Job(
                id="9",
                title="UI设计师",
                company="某创意设计工作室",
                location="杭州",
                salary="10-18K",
                experience="1-3年",
                education="本科",
                description="负责产品UI设计、交互设计，输出高保真设计稿和设计规范文档",
                requirements=["精通Figma/Sketch", "具备良好的审美观", "了解前端技术基础", "有移动端设计经验优先"],
                skills=["Figma", "Sketch", "Adobe XD", "交互设计", "设计系统", "原型设计"],
                source="示例数据",
                crawl_time=datetime.now().isoformat()
            ),
            Job(
                id="10",
                title="Golang开发工程师",
                company="某区块链公司",
                location="上海",
                salary="20-35K",
                experience="3-5年",
                education="本科",
                description="负责高性能后端服务开发，设计并实现分布式系统核心模块",
                requirements=["精通Golang", "熟悉微服务架构", "有RPC/gRPC经验", "了解分布式一致性算法"],
                skills=["Golang", "gRPC", "微服务", "Redis", "Kafka", "etcd"],
                source="示例数据",
                crawl_time=datetime.now().isoformat()
            ),
            Job(
                id="11",
                title="测试开发工程师",
                company="某大型互联网公司",
                location="北京",
                salary="15-25K",
                experience="1-3年",
                education="本科",
                description="负责自动化测试框架搭建、CI/CD集成测试，提升产品质量和交付效率",
                requirements=["熟悉软件测试理论", "掌握Python/Java至少一种语言", "有Selenium/Playwright经验", "了解性能测试"],
                skills=["Python", "Selenium", "JMeter", "pytest", "CI/CD", "API测试"],
                source="示例数据",
                crawl_time=datetime.now().isoformat()
            ),
            Job(
                id="12",
                title="iOS开发工程师",
                company="某移动互联网公司",
                location="广州",
                salary="15-25K",
                experience="1-3年",
                education="本科",
                description="负责iOS客户端开发和维护，参与新技术调研和架构升级",
                requirements=["精通Swift/Objective-C", "熟悉iOS框架和SDK", "了解设计模式", "有上架App Store经验"],
                skills=["Swift", "Objective-C", "UIKit", "SwiftUI", "Core Data", "Xcode"],
                source="示例数据",
                crawl_time=datetime.now().isoformat()
            ),
            Job(
                id="13",
                title="数据工程师",
                company="某电商公司",
                location="深圳",
                salary="18-30K",
                experience="3-5年",
                education="本科",
                description="负责数据仓库搭建、ETL流程开发和数据平台建设，支撑业务数据分析需求",
                requirements=["精通SQL", "熟悉Hadoop/Spark生态", "有数据仓库建模经验", "了解实时数据处理"],
                skills=["SQL", "Spark", "Hive", "Flink", "Airflow", "数据建模"],
                source="示例数据",
                crawl_time=datetime.now().isoformat()
            ),
            Job(
                id="14",
                title="DevOps工程师",
                company="某金融科技公司",
                location="杭州",
                salary="20-35K",
                experience="3-5年",
                education="本科",
                description="负责云平台基础设施建设、自动化运维体系搭建，推动研发效能提升",
                requirements=["精通AWS/阿里云等云平台", "熟悉IaC工具(Terraform)", "有GitOps实践经验", "具备安全防护意识"],
                skills=["AWS", "Terraform", "GitLab CI", "Kubernetes", "Helm", "安全加固"],
                source="示例数据",
                crawl_time=datetime.now().isoformat()
            ),
            Job(
                id="15",
                title="全栈开发工程师",
                company="某创业公司",
                location="成都",
                salary="14-24K",
                experience="1-3年",
                education="本科",
                description="负责前后端全栈开发，从需求分析到上线全流程参与，适合喜欢快速成长的开发者",
                requirements=["熟悉React/Vue前端框架", "掌握Python/Node.js后端开发", "了解数据库设计", "有独立开发项目经验"],
                skills=["React", "Node.js", "Python", "PostgreSQL", "Docker", "AWS"],
                source="示例数据",
                crawl_time=datetime.now().isoformat()
            )
        ]

        cls._append_jobs(sample_jobs)

    @classmethod
    def import_jobs(cls, jobs_data: List[dict]) -> dict:
        """
        导入职位数据，集成验证与去重功能

        Args:
            jobs_data: 职位数据列表（字典格式）

        Returns:
            dict: 导入结果统计

        Raises:
            ValueError: 当数据格式无效时
        """
        if not isinstance(jobs_data, list):
            raise ValueError("导入数据必须是数组格式")

        # 验证并转换数据
        valid_jobs = []
        invalid_count = 0
        for i, job_data in enumerate(jobs_data):
            try:
                job = cls.create_validated_job(job_data)
                if job:
                    valid_jobs.append(job)
                else:
                    invalid_count += 1
                    logger.warning(f"第{i+1}条数据验证失败，跳过")
            except Exception as e:
                invalid_count += 1
                logger.warning(f"第{i+1}条数据格式无效: {str(e)}")

        new_count, duplicate_count, _ = cls._append_jobs(valid_jobs)

        return {
            "message": f"导入完成",
            "total_received": len(jobs_data),
            "valid_count": len(valid_jobs),
            "invalid_count": invalid_count,
            "new_imported": new_count,
            "duplicates_skipped": duplicate_count
        }

    @classmethod
    def export_jobs(cls, keyword: Optional[str] = None, location: Optional[str] = None) -> dict:
        """
        导出职位数据

        Args:
            keyword: 可选的关键词过滤
            location: 可选的位置过滤

        Returns:
            dict: 导出结果，包含总数量和职位数据
        """
        jobs = cls._filter_jobs(keyword, location)

        return {
            "total": len(jobs),
            "jobs": [job.model_dump() for job in jobs],
            "exported_at": datetime.now().isoformat()
        }

    @classmethod
    def get_cache_status(cls) -> dict:
        """
        获取缓存状态信息

        Returns:
            dict: 缓存状态
        """
        if cls._cache is None:
            return {"cached": False, "entries": 0}

        return {
            "cached": True,
            "entries": len(cls._cache.data),
            "created_at": cls._cache.created_at,
            "expires_at": cls._cache.expires_at,
            "is_expired": cls._cache.is_expired()
        }
