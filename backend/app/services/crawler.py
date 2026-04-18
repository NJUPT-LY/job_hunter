import requests
from bs4 import BeautifulSoup
from typing import List
import uuid
import time
from datetime import datetime
from app.models.schemas import Job


class JobCrawler:
    
    @classmethod
    async def crawl(cls, keyword: str, max_pages: int = 3) -> List[Job]:
        jobs = []
        
        jobs.extend(await cls._crawl_mock(keyword))
        
        return jobs
    
    @classmethod
    async def _crawl_mock(cls, keyword: str) -> List[Job]:
        time.sleep(0.5)
        
        mock_jobs = {
            "前端": [
                {
                    "title": "前端开发工程师（应届生）",
                    "company": "字节跳动",
                    "location": "北京",
                    "salary": "15-20K",
                    "experience": "不限",
                    "education": "本科",
                    "description": "参与抖音/头条等核心产品的前端开发工作，与产品经理、设计师紧密合作，持续优化用户体验。负责高质量、可维护的前端代码编写，参与前端技术选型和架构设计。",
                    "requirements": [
                        "计算机相关专业本科及以上学历",
                        "熟练掌握HTML5/CSS3/JavaScript ES6+",
                        "熟悉React/Vue/Angular至少一种框架",
                        "了解前端工程化、组件化开发",
                        "具备良好的代码规范和团队协作能力"
                    ],
                    "skills": ["HTML5", "CSS3", "JavaScript", "React", "TypeScript", "Webpack", "Git"]
                },
                {
                    "title": "Web前端开发工程师",
                    "company": "腾讯",
                    "location": "深圳",
                    "salary": "18-25K",
                    "experience": "1年以下",
                    "education": "本科",
                    "description": "负责腾讯云相关产品的前端开发，参与产品需求评审和技术方案设计，持续优化产品性能和用户体验。",
                    "requirements": [
                        "本科及以上学历，计算机相关专业",
                        "扎实的前端基础，精通HTML/CSS/JavaScript",
                        "熟悉Vue或React生态",
                        "了解HTTP协议、浏览器原理",
                        "有GitHub开源项目者优先"
                    ],
                    "skills": ["JavaScript", "Vue", "React", "Node.js", "CSS", "HTTP", "Git"]
                }
            ],
            "后端": [
                {
                    "title": "Python后端开发工程师",
                    "company": "阿里巴巴",
                    "location": "杭州",
                    "salary": "20-30K",
                    "experience": "不限",
                    "education": "本科",
                    "description": "参与电商平台核心业务系统的后端开发，负责API设计、数据库设计、性能优化等工作。参与微服务架构设计与实现。",
                    "requirements": [
                        "计算机相关专业本科及以上学历",
                        "熟练掌握Python，熟悉Django/FastAPI等框架",
                        "熟悉MySQL/PostgreSQL等关系型数据库",
                        "了解Redis、消息队列等中间件",
                        "了解Linux操作系统，能独立部署服务"
                    ],
                    "skills": ["Python", "Django", "FastAPI", "MySQL", "Redis", "Docker", "Linux"]
                },
                {
                    "title": "Java开发工程师（校招）",
                    "company": "美团",
                    "location": "北京",
                    "salary": "18-25K",
                    "experience": "不限",
                    "education": "本科",
                    "description": "参与外卖、到店等核心业务系统的开发，参与系统架构设计与优化，保障系统高可用性。",
                    "requirements": [
                        "2024届应届毕业生，计算机相关专业",
                        "扎实的Java基础，了解JVM原理",
                        "熟悉Spring/Spring Boot框架",
                        "了解MySQL数据库基本操作",
                        "具备良好的算法和数据结构基础"
                    ],
                    "skills": ["Java", "Spring Boot", "MySQL", "Redis", "微服务", "算法", "数据结构"]
                }
            ],
            "数据分析": [
                {
                    "title": "数据分析师",
                    "company": "滴滴",
                    "location": "北京",
                    "salary": "15-22K",
                    "experience": "不限",
                    "education": "本科",
                    "description": "负责业务数据分析，搭建数据监控体系，输出分析报告，为业务决策提供数据支持。参与数据产品需求讨论。",
                    "requirements": [
                        "统计学、数学、计算机等相关专业",
                        "熟练使用SQL进行数据提取和分析",
                        "熟悉Python/R，掌握Pandas/NumPy等库",
                        "了解常用统计分析方法和数据可视化",
                        "具备良好的业务理解和沟通表达能力"
                    ],
                    "skills": ["SQL", "Python", "Pandas", "Tableau", "Excel", "统计学", "数据可视化"]
                }
            ],
            "产品": [
                {
                    "title": "产品助理/专员",
                    "company": "拼多多",
                    "location": "上海",
                    "salary": "12-18K",
                    "experience": "不限",
                    "education": "本科",
                    "description": "协助产品经理完成产品规划和设计，跟进产品上线进度，收集用户反馈并推动产品优化迭代。",
                    "requirements": [
                        "本科及以上学历，专业不限",
                        "对互联网产品有热情和见解",
                        "熟练使用Axure/Figma等原型工具",
                        "具备良好的逻辑思维和沟通能力",
                        "有产品相关实习经验者优先"
                    ],
                    "skills": ["产品规划", "Axure", "Figma", "数据分析", "用户研究", "原型设计", "沟通协作"]
                }
            ]
        }
        
        jobs = []
        for category, category_jobs in mock_jobs.items():
            if category in keyword or keyword in category:
                for job_data in category_jobs:
                    job = Job(
                        id=str(uuid.uuid4()),
                        title=job_data["title"],
                        company=job_data["company"],
                        location=job_data["location"],
                        salary=job_data["salary"],
                        experience=job_data["experience"],
                        education=job_data["education"],
                        description=job_data["description"],
                        requirements=job_data["requirements"],
                        skills=job_data["skills"],
                        source="模拟数据",
                        crawl_time=datetime.now().isoformat()
                    )
                    jobs.append(job)
        
        return jobs
