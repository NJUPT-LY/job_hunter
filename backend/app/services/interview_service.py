from typing import List
from app.models.schemas import InterviewQuestion, AnswerEvaluation
from app.services.ai_service import chat_completion
from app.utils.json_parser import parse_json_response


class InterviewService:

    @classmethod
    def get_questions(cls, job_category: str = "技术", interview_type: str = "技术面",
                     difficulty: str = "中等") -> List[InterviewQuestion]:
        questions = cls._get_question_bank()

        filtered = [q for q in questions if q.category == interview_type]

        filtered = [q for q in filtered if q.difficulty == difficulty]
        if interview_type == "技术面" and job_category in ("产品", "数据分析"):
            subject = "产品需求与优先级" if job_category == "产品" else "数据质量与分析方法"
            filtered = [InterviewQuestion(
                question=f"请结合一个项目说明你如何处理{subject}。",
                category=interview_type, difficulty=difficulty,
                hints=["项目背景", "采用的方法", "个人贡献", "结果与复盘"],
                evaluation_criteria=["方法合理性", "岗位知识", "表达清晰度"],
            )]

        return filtered[:10]

    @classmethod
    async def simulate_interview(cls, job_title: str, interview_type: str,
                                 user_answer: str = None, question_index: int = 0) -> dict:
        questions = cls._get_interview_questions_by_type(interview_type)
        if not 0 <= question_index < len(questions):
            raise ValueError("题目序号超出范围")
        if user_answer is None:
            return {"status": "started", "interview_type": interview_type,
                    "job_title": job_title, "current_question": questions[question_index],
                    "question_index": question_index, "total_questions": len(questions)}
        if not user_answer.strip():
            raise ValueError("回答不能为空")
        evaluation = await cls.evaluate_answer(questions[question_index], user_answer, job_title)
        next_index = question_index + 1
        finished = next_index >= len(questions)
        return {"status": "completed" if finished else "in_progress",
                "evaluation": evaluation, "score": evaluation["score"],
                "next_question": None if finished else questions[next_index],
                "question_index": next_index, "total_questions": len(questions),
                "ai_provider": evaluation["ai_provider"], "is_fallback": evaluation["is_fallback"]}

    @classmethod
    async def evaluate_answer(cls, question: str, answer: str, job_title: str) -> dict:
        # 尝试使用AI评估
        ai_result = await cls._ai_evaluate_answer(answer, question)
        if ai_result and not ai_result.get("is_fallback", False):
            result = ai_result.get("evaluation", {})
            result["ai_provider"] = ai_result.get("provider", "ai")
            result["is_fallback"] = False
            return result

        # 降级到规则引擎
        result = cls._evaluate_answer(answer, question)
        result["ai_provider"] = "rule_engine"
        result["is_fallback"] = True
        return result

    @classmethod
    async def _ai_evaluate_answer(cls, answer: str, question: str) -> dict:
        """使用AI评估面试回答，失败时返回None"""
        prompt = f"""
请评估以下面试回答：

问题：{question}

回答：{answer}

请从以下维度进行评估并返回JSON格式：
1. score: 分数(0-100)
2. feedback: 总体评价(字符串数组)
3. strengths: 优点(字符串数组)
4. weaknesses: 不足(字符串数组)
5. suggestions: 改进建议(字符串数组)

只返回JSON，不要有其他内容。
"""
        system_prompt = "你是一个专业的面试评估专家，能够准确评估候选人的回答质量。"

        try:
            result = await chat_completion(prompt, system_prompt)
            if result.get("is_fallback"):
                return result

            # 解析AI返回的JSON
            evaluation = parse_json_response(result.get("content", ""))
            result["evaluation"] = AnswerEvaluation.model_validate(evaluation).model_dump()
            return result
        except Exception:
            return None
    
    @classmethod
    def _evaluate_answer(cls, answer: str, question: str) -> dict:
        score = 60
        feedback = []
        strengths = []
        weaknesses = []
        
        if len(answer) > 100:
            score += 10
            strengths.append("回答内容详细充分")
        elif len(answer) < 30:
            score -= 10
            weaknesses.append("回答过于简短，建议展开说明")
        
        if "首先" in answer or "第一" in answer or "1." in answer:
            score += 5
            strengths.append("回答结构清晰，有条理")
        
        if any(kw in answer for kw in ["项目", "经验", "实践", "例子"]):
            score += 10
            strengths.append("能够结合实际经验说明")
        
        if not any(kw in answer for kw in ["因此", "所以", "总结", "总之"]):
            weaknesses.append("建议加入总结性陈述")
        
        score = max(0, min(100, score))
        
        return {
            "score": score,
            "feedback": feedback if feedback else ["回答基本完成要求"],
            "strengths": strengths if strengths else ["无明显亮点"],
            "weaknesses": weaknesses if weaknesses else ["无明显不足"],
            "suggestions": [
                "建议使用STAR法则组织回答",
                "建议加入具体数据或案例支撑",
                "建议注意回答的逻辑性和完整性"
            ]
        }
    
    @classmethod
    def _get_question_bank(cls) -> List[InterviewQuestion]:
        return [
            InterviewQuestion(
                question="请介绍一下你最熟悉的一个项目，你在其中承担了什么角色？",
                category="技术面",
                difficulty="简单",
                hints=["说明项目背景和目标", "描述你的具体职责", "分享遇到的挑战和解决方案"],
                evaluation_criteria=["项目描述的清晰度", "个人贡献的明确性", "技术深度"]
            ),
            InterviewQuestion(
                question="什么是HTTP协议？请描述一次完整的HTTP请求过程。",
                category="技术面",
                difficulty="中等",
                hints=["DNS解析", "TCP三次握手", "HTTP请求发送", "服务器响应", "连接关闭"],
                evaluation_criteria=["知识完整性", "表述准确性", "逻辑清晰度"]
            ),
            InterviewQuestion(
                question="请解释一下什么是闭包，它有什么应用场景？",
                category="技术面",
                difficulty="中等",
                hints=["函数和作用域的关系", "变量生命周期", "实际应用如防抖节流"],
                evaluation_criteria=["概念理解深度", "实例说明", "应用能力"]
            ),
            InterviewQuestion(
                question="如果线上系统突然出现大量500错误，你会如何排查？",
                category="技术面",
                difficulty="困难",
                hints=["查看日志", "监控系统", "回滚策略", "影响评估"],
                evaluation_criteria=["排查思路", "优先级判断", "应急处理能力"]
            ),
            InterviewQuestion(
                question="你为什么选择应聘我们公司？你对我们公司有什么了解？",
                category="HR面",
                difficulty="简单",
                hints=["公司业务范围", "公司文化价值观", "个人职业规划匹配"],
                evaluation_criteria=["准备充分度", "求职动机", "匹配度认知"]
            ),
            InterviewQuestion(
                question="请描述一次你与团队成员发生分歧的经历，你是如何处理的？",
                category="HR面",
                difficulty="中等",
                hints=["具体情境描述", "分歧的本质", "解决方案", "最终结果和反思"],
                evaluation_criteria=["沟通能力", "冲突解决能力", "团队协作意识"]
            ),
            InterviewQuestion(
                question="你未来3-5年的职业规划是什么？",
                category="HR面",
                difficulty="简单",
                hints=["短期目标", "长期目标", "与公司的契合点", "具体行动计划"],
                evaluation_criteria=["规划合理性", "目标明确性", "可执行性"]
            ),
            InterviewQuestion(
                question="请描述一个你遇到的最有挑战性的问题，你是如何解决的？",
                category="行为面",
                difficulty="中等",
                hints=["挑战的具体内容", "困难点在哪里", "解决思路和方法", "最终成果"],
                evaluation_criteria=["问题分析能力", "解决能力", "抗压能力"]
            ),
            InterviewQuestion(
                question="如果你的上级给你安排了一个你从未接触过的任务，你会怎么做？",
                category="行为面",
                difficulty="中等",
                hints=["态度", "学习途径", "资源寻找", "沟通反馈"],
                evaluation_criteria=["学习态度", "主动性", "沟通能力"]
            ),
            InterviewQuestion(
                question="请描述一次你失败的经历，你从中学到了什么？",
                category="行为面",
                difficulty="困难",
                hints=["失败的具体情境", "失败原因分析", "反思和收获", "后续改进"],
                evaluation_criteria=["自我反思能力", "成长意识", "诚实度"]
            )
        ]
    
    @classmethod
    def _get_interview_questions_by_type(cls, interview_type: str) -> List[str]:
        questions_map = {
            "技术面": [
                "请介绍一下你的技术栈，你最擅长哪个方向？",
                "请描述一个你印象最深的技术难题，你是如何解决的？",
                "你在项目中是如何保证代码质量的？",
                "请解释一下你简历中提到的某个项目的技术架构。"
            ],
            "HR面": [
                "请做一个简单的自我介绍。",
                "你为什么选择这个岗位？你的优势是什么？",
                "你期望的薪资是多少？",
                "你对加班怎么看？"
            ],
            "行为面": [
                "描述一次你主动承担责任并完成任务的经历。",
                "当你同时面对多个任务时，你是如何优先级排序的？",
                "描述一次你需要快速学习新知识的经历。",
                "你和同事意见不合时，通常如何处理？"
            ]
        }
        
        return questions_map.get(interview_type, questions_map["技术面"])
