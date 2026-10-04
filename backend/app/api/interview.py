from fastapi import APIRouter, HTTPException
from typing import List, Literal
from app.models.schemas import InterviewQuestion, SimulateInterviewRequest, EvaluateAnswerRequest
from app.services.interview_service import InterviewService

router = APIRouter()


@router.get("/questions", response_model=List[InterviewQuestion])
def get_questions(
    job_category: Literal["技术", "产品", "数据分析"] = "技术",
    interview_type: Literal["技术面", "HR面", "行为面"] = "技术面",
    difficulty: Literal["简单", "中等", "困难"] = "中等"
):
    questions = InterviewService.get_questions(job_category, interview_type, difficulty)
    return questions


@router.post("/simulate")
async def simulate_interview(request: SimulateInterviewRequest):
    try:
        return await InterviewService.simulate_interview(
            request.job_title, request.interview_type, request.user_answer, request.question_index,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/evaluate")
async def evaluate_answer(request: EvaluateAnswerRequest):
    result = await InterviewService.evaluate_answer(request.question, request.answer, request.job_title)
    return result
