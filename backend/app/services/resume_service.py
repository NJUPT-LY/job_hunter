from typing import Optional, List
from app.models.schemas import ResumeTemplate


class ResumeService:
    
    @classmethod
    def get_templates(cls, category: Optional[str] = None) -> List[ResumeTemplate]:
        templates = [
            ResumeTemplate(
                id="tech_1",
                name="技术研发岗模板",
                category="技术",
                content="姓名 | 电话 | 邮箱\n\n教育背景\n- 学校 | 专业 | 学历 | 时间\n\n技术栈\n- 编程语言：\n- 框架工具：\n- 其他技能：\n\n项目经历\n- 项目名称\n  - 项目描述：\n  - 技术栈：\n  - 我的贡献：（使用STAR法则）\n  - 成果：\n\n实习/工作经历\n- 公司 | 职位 | 时间\n  - 工作内容：\n  - 成果：\n\n校园经历/荣誉\n- \n\n自我评价\n- "
            ),
            ResumeTemplate(
                id="product_1",
                name="产品经理岗模板",
                category="产品",
                content="姓名 | 电话 | 邮箱\n\n教育背景\n- 学校 | 专业 | 学历 | 时间\n\n核心能力\n- 产品规划：\n- 数据分析：\n- 工具技能：Axure/Figma/...\n\n项目经历\n- 项目名称\n  - 项目背景：\n  - 我的角色：\n  - 工作内容：（需求分析→原型设计→跟进上线）\n  - 成果数据：\n\n实习经历\n- 公司 | 职位 | 时间\n  - 工作内容：\n  - 成果：\n\n产品分析作品\n- \n\n自我评价\n- "
            ),
            ResumeTemplate(
                id="data_1",
                name="数据分析岗模板",
                category="数据分析",
                content="姓名 | 电话 | 邮箱\n\n教育背景\n- 学校 | 专业 | 学历 | 时间\n\n技术技能\n- 编程语言：Python/R/SQL\n- 分析工具：Pandas/Tableau/Excel\n- 其他：\n\n项目经历\n- 项目名称\n  - 项目背景：\n  - 分析方法：\n  - 数据来源：\n  - 分析结论：\n  - 业务价值：\n\n实习经历\n- 公司 | 职位 | 时间\n  - 工作内容：\n  - 成果：\n\n数据分析作品集\n- GitHub/Kaggle链接\n\n自我评价\n- "
            ),
            ResumeTemplate(
                id="general_1",
                name="通用简历模板",
                category="通用",
                content="姓名 | 电话 | 邮箱\n\n教育背景\n- 学校 | 专业 | 学历 | 时间\n\n技能特长\n- \n\n项目/实践经历\n- 项目名称\n  - 情境（Situation）：\n  - 任务（Task）：\n  - 行动（Action）：\n  - 结果（Result）：\n\n实习/工作经历\n- 公司 | 职位 | 时间\n  - STAR法则描述\n\n校园经历\n- \n\n荣誉奖项\n- \n\n自我评价\n- "
            )
        ]
        
        if category:
            templates = [t for t in templates if t.category == category]
        
        return templates
    
    @classmethod
    async def evaluate_resume(cls, resume_content: str, target_job: str) -> dict:
        score = cls._calculate_resume_score(resume_content, target_job)
        suggestions = cls._generate_resume_suggestions(resume_content, target_job)
        
        return {
            "overall_score": score,
            "category_scores": {
                "内容完整性": cls._check_completeness(resume_content),
                "与岗位匹配度": cls._check_match(resume_content, target_job),
                "STAR法则使用": cls._check_star_method(resume_content),
                "关键词优化": cls._check_keywords(resume_content, target_job)
            },
            "suggestions": suggestions,
            "strengths": cls._find_strengths(resume_content),
            "weaknesses": cls._find_weaknesses(resume_content)
        }
    
    @classmethod
    async def optimize_resume(cls, resume_content: str, target_job: str) -> dict:
        suggestions = cls._generate_optimization_suggestions(resume_content, target_job)
        optimized_content = cls._apply_optimizations(resume_content, suggestions)
        
        return {
            "original_content": resume_content,
            "optimized_content": optimized_content,
            "changes": suggestions
        }
    
    @classmethod
    def _calculate_resume_score(cls, content: str, target_job: str) -> int:
        score = 60
        
        if len(content) > 200:
            score += 5
        if "教育背景" in content:
            score += 5
        if "项目" in content or "实习" in content:
            score += 5
        if "S" in content and "T" in content and "A" in content and "R" in content:
            score += 10
        elif "情境" in content or "任务" in content or "行动" in content or "结果" in content:
            score += 5
        
        job_keywords = ["Python", "Java", "JavaScript", "React", "Vue", "SQL", "数据分析", "产品"]
        for kw in job_keywords:
            if kw.lower() in content.lower():
                score += 2
        
        return min(score, 100)
    
    @classmethod
    def _check_completeness(cls, content: str) -> int:
        sections = ["教育背景", "项目", "实习", "技能", "自我"]
        count = sum(1 for s in sections if s in content)
        return int(count / len(sections) * 100)
    
    @classmethod
    def _check_match(cls, content: str, target_job: str) -> int:
        job_skills = {
            "前端": ["HTML", "CSS", "JavaScript", "React", "Vue"],
            "后端": ["Python", "Java", "Spring", "MySQL", "Redis"],
            "数据": ["SQL", "Python", "Pandas", "Tableau", "Excel"],
            "产品": ["产品", "原型", "Axure", "Figma", "需求"]
        }
        
        for category, skills in job_skills.items():
            if category in target_job:
                matched = sum(1 for s in skills if s.lower() in content.lower())
                return int(matched / len(skills) * 100)
        return 50
    
    @classmethod
    def _check_star_method(cls, content: str) -> int:
        star_indicators = ["Situation", "Task", "Action", "Result", "情境", "任务", "行动", "结果"]
        count = sum(1 for s in star_indicators if s in content)
        return min(int(count / 4 * 100), 100)
    
    @classmethod
    def _check_keywords(cls, content: str, target_job: str) -> int:
        job_keywords_map = {
            "前端": ["前端", "HTML", "CSS", "JavaScript", "React", "Vue", "组件化"],
            "后端": ["后端", "API", "数据库", "Python", "Java", "微服务"],
            "数据": ["数据分析", "SQL", "Python", "可视化", "统计", "报告"],
            "产品": ["产品", "需求", "原型", "用户", "迭代", "分析"]
        }
        
        for category, keywords in job_keywords_map.items():
            if category in target_job:
                matched = sum(1 for kw in keywords if kw.lower() in content.lower())
                return int(matched / len(keywords) * 100)
        return 50
    
    @classmethod
    def _generate_resume_suggestions(cls, content: str, target_job: str) -> list:
        suggestions = []
        
        if len(content) < 200:
            suggestions.append("简历内容较少，建议补充更多项目经历和成果数据")
        
        if "教育背景" not in content:
            suggestions.append("缺少教育背景，请补充学校、专业、学历等信息")
        
        if "项目" not in content and "实习" not in content:
            suggestions.append("缺少项目或实习经历，建议补充相关实践经验")
        
        if not any(word in content for word in ["情境", "Situation", "任务", "Task", "行动", "Action", "结果", "Result"]):
            suggestions.append("建议使用STAR法则描述项目经历，突出个人贡献和成果")
        
        if not any(word in content for word in ["%", "提升", "优化", "减少", "增加", "完成"]):
            suggestions.append("建议在项目经历中加入量化数据，如提升效率XX%、完成XX功能等")
        
        suggestions.append(f"建议针对{target_job}岗位，突出相关技能和项目经验")
        
        return suggestions
    
    @classmethod
    def _find_strengths(cls, content: str) -> list:
        strengths = []
        if len(content) > 500:
            strengths.append("简历内容丰富详实")
        if "项目" in content and "实习" in content:
            strengths.append("同时具备项目经验和实习经验")
        if any(word in content for word in ["%", "提升", "优化"]):
            strengths.append("使用了量化数据描述成果")
        if "GitHub" in content or "github" in content.lower():
            strengths.append("提供了GitHub链接，展示了开源贡献")
        return strengths
    
    @classmethod
    def _find_weaknesses(cls, content: str) -> list:
        weaknesses = []
        if len(content) < 300:
            weaknesses.append("简历内容较为简略")
        if "项目" not in content:
            weaknesses.append("缺少项目经历")
        if not any(word in content for word in ["情境", "Situation", "STAR"]):
            weaknesses.append("未使用STAR法则描述经历")
        return weaknesses
    
    @classmethod
    def _generate_optimization_suggestions(cls, content: str, target_job: str) -> list:
        suggestions = []
        
        if "负责" in content:
            suggestions.append("将'负责XXX'改为'通过XXX实现了XXX，提升了XX%'")
        
        if "参与" in content:
            suggestions.append("将'参与XXX'改为具体描述个人贡献，如'在XXX中独立完成XXX模块'")
        
        suggestions.append("在项目描述中加入具体数据支撑")
        suggestions.append("将技能与目标岗位要求对齐")
        
        return suggestions
    
    @classmethod
    def _apply_optimizations(cls, content: str, suggestions: list) -> str:
        optimized = content
        
        optimized = optimized.replace("负责", "主导完成")
        optimized = optimized.replace("参与", "在团队中负责")
        
        return optimized
