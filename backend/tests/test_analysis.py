import json
import unittest
from unittest.mock import AsyncMock, patch

from common import FileFixture, make_job
from app.services.job_service import JobService
from app.services.analyzer import JobAnalyzer
from app.services.action_generator import ActionPlanGenerator
from app.services.interview_service import InterviewService
from app.services.resume_service import ResumeService
from app.utils.json_parser import parse_json_response


class RuleAnalysisTests(FileFixture, unittest.TestCase):
    def test_skill_levels_keep_highest_requirement(self):
        JobService._save_jobs([make_job(skills=["Python", "SQL", "数据分析"],
                                      requirements=["精通Python", "了解python", "了解SQL"])])
        analysis = JobAnalyzer.analyze_job("1")
        self.assertEqual(analysis.skill_levels["Python"], "精通")
        self.assertEqual(analysis.skill_levels["SQL"], "入门")
        self.assertEqual(analysis.skill_levels["数据分析"], "进阶")
        self.assertIn("数据分析", [item["name"] for item in analysis.hard_skills])

    def test_skill_extraction_uses_word_boundaries(self):
        skills = JobAnalyzer._extract_skills_from_text("JavaScript、MongoDB，代码放在GitHub，使用TypeScript")
        self.assertEqual(skills, ["JavaScript", "TypeScript", "MongoDB"])

    def test_salary_numbers_do_not_change_experience_level(self):
        self.assertEqual(JobAnalyzer._detect_experience_level("薪资30-50K，要求3-5年经验"), "中级（3-5年）")
        self.assertEqual(JobAnalyzer._detect_experience_level("薪资30K，10年经验"), "高级（5年以上）")
        self.assertEqual(JobAnalyzer._detect_experience_level("城市不限，薪资50K"), "未明确要求")

    def test_skill_gap_strips_user_input(self):
        JobService._save_jobs([make_job()])
        result = JobAnalyzer.analyze_skill_gap({"skills": [" python "]}, "1")
        self.assertEqual(result.match_score, 50)

    def test_data_engineer_gets_data_plan(self):
        self.assertEqual(ActionPlanGenerator._detect_category("数据工程师"), "数据分析")

    def test_question_filters_respect_exact_difficulty_and_category(self):
        questions = InterviewService.get_questions("技术", "技术面", "简单")
        self.assertTrue(questions)
        self.assertTrue(all(question.difficulty == "简单" for question in questions))
        product = InterviewService.get_questions("产品", "技术面", "中等")
        self.assertIn("产品需求", product[0].question)

    def test_json_with_brackets_in_strings_is_parsed_correctly(self):
        result = parse_json_response('说明：```json\n{"text": "内容含 } 与 [", "items": []}\n```')
        self.assertEqual(result["text"], "内容含 } 与 [")

    def test_resume_star_dimensions_do_not_count_translations_twice(self):
        self.assertEqual(ResumeService._check_star_method("Situation 情境，Task 任务"), 50)
        self.assertEqual(ResumeService._check_star_method("React CSS HTML"), 0)


class StructuredResponseTests(unittest.IsolatedAsyncioTestCase):
    async def test_invalid_jd_shape_falls_back_to_rules(self):
        with patch("app.services.analyzer.chat_completion", AsyncMock(return_value={
            "is_fallback": False, "content": '{"required_skills": "Python"}'
        })):
            result = await JobAnalyzer.parse_jd("负责Python开发，本科，3年经验")
        self.assertTrue(result["is_fallback"])
        self.assertIn("Python", result["required_skills"])

    async def test_valid_jd_preserves_structured_fields(self):
        data = dict(summary="后端岗位", key_responsibilities=["开发服务"], required_skills=["Python"],
                    experience_level="3年", education_requirement="本科", plain_language="开发后端服务")
        with patch("app.services.analyzer.chat_completion", AsyncMock(return_value={
            "is_fallback": False, "provider": "test", "content": json.dumps(data)
        })):
            result = await JobAnalyzer.parse_jd("岗位描述")
        self.assertFalse(result["is_fallback"])
        self.assertEqual(result["summary"], "后端岗位")

    async def test_empty_model_plan_uses_template(self):
        with patch("app.services.action_generator.chat_completion", AsyncMock(return_value={
            "is_fallback": False, "content": "[]"
        })):
            plan = await ActionPlanGenerator.generate("前端开发", {})
        self.assertGreaterEqual(len(plan), 3)

    async def test_invalid_model_score_uses_rule_evaluation(self):
        with patch("app.services.interview_service.chat_completion", AsyncMock(return_value={
            "is_fallback": False, "content": '{"score": 999, "strengths": "错误类型"}'
        })):
            result = await InterviewService.evaluate_answer("问题", "回答", "前端")
        self.assertTrue(result["is_fallback"])
        self.assertLessEqual(result["score"], 100)
        self.assertIsInstance(result["strengths"], list)

    async def test_simulation_evaluates_current_question_and_finishes(self):
        evaluator = AsyncMock(return_value={"score": 80, "ai_provider": "test", "is_fallback": False})
        questions = InterviewService._get_interview_questions_by_type("技术面")
        with patch.object(InterviewService, "evaluate_answer", evaluator):
            result = await InterviewService.simulate_interview("前端", "技术面", "回答", 2)
            evaluator.assert_awaited_with(questions[2], "回答", "前端")
            self.assertEqual(result["next_question"], questions[3])
            end = await InterviewService.simulate_interview("前端", "技术面", "回答", 3)
        self.assertEqual(end["status"], "completed")
        self.assertIsNone(end["next_question"])
        with self.assertRaises(ValueError):
            await InterviewService.simulate_interview("前端", "技术面", "回答", 4)

    async def test_resume_cleanup_does_not_invent_responsibility(self):
        content = " 参与项目，负责接口开发。  \n"
        result = await ResumeService.optimize_resume(content, "后端")
        self.assertEqual(result["optimized_content"], content.strip())
        self.assertNotIn("主导", result["optimized_content"])
