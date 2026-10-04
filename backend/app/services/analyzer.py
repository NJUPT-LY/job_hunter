from typing import Optional, List, Dict
import re
from app.models.schemas import JobAnalysis, SkillGap, ParsedJD
from app.services.job_service import JobService
from app.services.ai_service import chat_completion
from app.utils.json_parser import parse_json_response
from app.utils.skill_matching import contains_skill


class JobAnalyzer:
    
    @classmethod
    def analyze_job(cls, job_id: str) -> Optional[JobAnalysis]:
        job = JobService.get_job(job_id)
        if not job:
            return None
        
        hard_skills = []
        soft_skills = []
        skill_levels = {}
        
        tech_keywords = {
            "入门": ["了解", "熟悉", "接触过"],
            "进阶": ["熟练", "掌握", "使用", "开发"],
            "精通": ["精通", "深入", "专家", "架构"]
        }
        
        soft_skill_words = ["沟通", "协作", "团队", "表达", "领导", "管理", "思维", "创新"]
        
        for skill in job.skills:
            is_soft = any(sw in skill for sw in soft_skill_words)
            if is_soft:
                soft_skills.append({"name": skill, "importance": "高"})
            else:
                hard_skills.append({"name": skill, "importance": "高"})
        
        for req in job.requirements:
            for level, keywords in tech_keywords.items():
                for keyword in keywords:
                    if keyword in req:
                        for skill in job.skills:
                            if contains_skill(req, skill):
                                ranks = {"入门": 1, "进阶": 2, "精通": 3}
                                if ranks[level] > ranks.get(skill_levels.get(skill), 0):
                                    skill_levels[skill] = level
        
        for skill in hard_skills:
            skill_levels.setdefault(skill["name"], "进阶")
        
        real_work = cls._extract_real_work(job)
        
        career_paths = cls._generate_career_path(job.title)
        
        summary = cls._generate_summary(job)
        
        return JobAnalysis(
            job_id=job_id,
            real_work_content=real_work,
            hard_skills=hard_skills,
            soft_skills=soft_skills,
            skill_levels=skill_levels,
            career_path=career_paths,
            summary=summary
        )
    
    @classmethod
    def analyze_skill_gap(cls, user_skills: dict, job_id: str) -> SkillGap:
        job = JobService.get_job(job_id)
        if not job:
            return SkillGap()
        
        user_skill_names = {s.strip().casefold() for s in user_skills.get("skills", [])}
        
        matched = []
        missing = []
        
        for skill in job.skills:
            if skill.strip().casefold() in user_skill_names:
                matched.append({"skill": skill, "status": "已掌握"})
            else:
                missing.append({"skill": skill, "priority": "高"})
        
        total = len(job.skills)
        matched_count = len(matched)
        match_score = (matched_count / total * 100) if total > 0 else 0
        
        suggestions = []
        if missing:
            suggestions.append(f"还需要掌握{len(missing)}个技能：{', '.join([m['skill'] for m in missing[:5]])}")
            suggestions.append("建议按照技能重要性顺序学习，优先掌握核心技能")
            suggestions.append("可以通过项目实践来快速提升技能")
        
        return SkillGap(
            matched_skills=matched,
            missing_skills=missing,
            match_score=round(match_score, 2),
            suggestions=suggestions
        )
    
    @classmethod
    async def parse_jd(cls, jd_text: str) -> dict:
        # 尝试使用AI解析JD
        ai_result = await cls._ai_parse_jd(jd_text)
        if ai_result and not ai_result.get("is_fallback", False):
            result = ai_result.get("parsed", {})
            result["ai_provider"] = ai_result.get("provider", "ai")
            result["is_fallback"] = False
            return result
        
        # 降级到规则引擎
        return {
            "summary": "这是一个基于规则引擎的JD解析结果",
            "key_responsibilities": cls._extract_responsibilities(jd_text),
            "required_skills": cls._extract_skills_from_text(jd_text),
            "experience_level": cls._detect_experience_level(jd_text),
            "education_requirement": cls._detect_education(jd_text),
            "plain_language": cls._translate_to_plain_language(jd_text),
            "ai_provider": "rule_engine",
            "is_fallback": True,
        }
    
    @classmethod
    async def _ai_parse_jd(cls, jd_text: str) -> dict:
        """使用AI解析职位描述"""
        prompt = f"""
请分析以下职位描述(JD)并返回JSON格式：

{jd_text}

请返回以下字段：
- summary: 职位总结(一句话)
- key_responsibilities: 主要职责(字符串数组)
- required_skills: 需要的技能(字符串数组)
- experience_level: 经验要求(字符串)
- education_requirement: 学历要求(字符串)
- plain_language: 用通俗语言重述职位内容(字符串)

只返回JSON，不要有其他内容。
"""
        system_prompt = "你是一个专业的JD分析专家，能够准确解析职位描述。"
        
        try:
            result = await chat_completion(prompt, system_prompt)
            if result.get("is_fallback"):
                return result
            
            parsed = parse_json_response(result.get("content", ""))
            result["parsed"] = ParsedJD.model_validate(parsed).model_dump()
            return result
        except Exception:
            return None
    
    @classmethod
    def _extract_real_work(cls, job) -> List[str]:
        desc = job.description
        
        work_items = []
        if "开发" in desc:
            work_items.append("编写代码实现产品功能")
        if "设计" in desc:
            work_items.append("参与系统/产品方案设计")
        if "优化" in desc:
            work_items.append("持续优化系统性能或用户体验")
        if "需求" in desc:
            work_items.append("参与产品需求讨论和评审")
        if "分析" in desc:
            work_items.append("进行数据分析或技术分析")
        if "协调" in desc or "合作" in desc:
            work_items.append("与团队成员协作推进项目")
        if "维护" in desc:
            work_items.append("维护和优化现有系统")
        if "文档" in desc:
            work_items.append("编写技术文档或使用文档")
        
        if not work_items:
            work_items = [
                "完成日常工作任务",
                "参与团队协作和沟通",
                "持续学习和提升技能"
            ]
        
        return work_items
    
    @classmethod
    def _generate_career_path(cls, job_title: str) -> List[str]:
        if "前端" in job_title:
            return ["初级前端开发", "中级前端开发", "高级前端开发", "前端技术专家", "前端架构师"]
        elif "后端" in job_title or "Python" in job_title or "Java" in job_title:
            return ["初级后端开发", "中级后端开发", "高级后端开发", "后端技术专家", "系统架构师"]
        elif "数据" in job_title:
            return ["初级数据分析师", "数据分析师", "高级数据分析师", "数据科学家", "数据分析专家"]
        elif "产品" in job_title:
            return ["产品助理", "产品经理", "高级产品经理", "产品总监", "产品副总裁"]
        elif "测试" in job_title:
            return ["初级测试工程师", "测试工程师", "高级测试工程师", "测试专家", "测试架构师"]
        else:
            return ["初级岗位", "中级岗位", "高级岗位", "专家岗位", "管理岗位"]
    
    @classmethod
    def _generate_summary(cls, job) -> str:
        return f"这是一份{job.title}职位，由{job.company}发布，工作地点在{job.location}，薪资范围{job.salary}。主要要求：{', '.join(job.requirements[:3])}。"
    
    @classmethod
    def _extract_responsibilities(cls, text: str) -> List[str]:
        responsibilities = []
        lines = text.replace('。', '。\n').replace('；', ';\n').split('\n')
        for line in lines:
            line = line.strip()
            if any(kw in line for kw in ['负责', '参与', '完成', '推进', '协助']):
                responsibilities.append(line)
        return responsibilities if responsibilities else ["根据岗位描述执行相关工作"]
    
    @classmethod
    def _extract_skills_from_text(cls, text: str) -> List[str]:
        tech_skills = [
            "Python", "Java", "JavaScript", "TypeScript", "C++", "Go", "SQL",
            "HTML", "CSS", "React", "Vue", "Angular", "Django", "Flask", "Spring",
            "MySQL", "Redis", "MongoDB", "Docker", "Kubernetes", "Git",
            "Linux", "AWS", "Azure", "Tableau", "Excel", "Figma", "Axure"
        ]
        found = []
        for skill in tech_skills:
            if contains_skill(text, skill):
                found.append(skill)
        return found
    
    @classmethod
    def _detect_experience_level(cls, text: str) -> str:
        if "应届" in text or "经验不限" in text or "不限经验" in text or "无经验要求" in text:
            return "应届生/无经验要求"
        match = re.search(r"(\d+)\s*(?:[-~–至到]\s*\d+)?\s*年", text)
        if match:
            years = int(match.group(1))
            if years == 0:
                return "应届生/无经验要求"
            if years < 3:
                return "初级（1-3年）"
            if years < 5:
                return "中级（3-5年）"
            return "高级（5年以上）"
        return "未明确要求"
    
    @classmethod
    def _detect_education(cls, text: str) -> str:
        if "博士" in text:
            return "博士"
        elif "硕士" in text:
            return "硕士及以上"
        elif "本科" in text:
            return "本科及以上"
        elif "大专" in text:
            return "大专及以上"
        return "未明确要求"
    
    @classmethod
    def _translate_to_plain_language(cls, text: str) -> str:
        translations = [
            ("负责", "你需要做："),
            ("参与", "你要加入团队一起做："),
            ("精通", "非常熟练地使用"),
            ("熟悉", "能够正常使用"),
            ("了解", "知道基本概念"),
            ("熟练掌握", "能够独立使用")
        ]
        
        plain_text = text
        for original, translated in translations:
            plain_text = plain_text.replace(original, translated)
        
        return plain_text
