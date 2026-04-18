from fastapi import APIRouter
from typing import List
from app.models.schemas import InterviewQuestion
from app.services.interview_service import InterviewService

router = APIRouter()


@router.get("/questions", response_model=List[InterviewQuestion])
async def get_questions(
    job_category: str = "技术",
    interview_type: str = "技术面",
    difficulty: str = "中等"
):
    questions = InterviewService.get_questions(job_category, interview_type, difficulty)
    return questions


@router.post("/simulate")
async def simulate_interview(job_title: str, interview_type: str, user_answer: str = None):
    result = await InterviewService.simulate_interview(job_title, interview_type, user_answer)
    return result


@router.post("/evaluate")
async def evaluate_answer(question: str, answer: str, job_title: str):
    result = await InterviewService.evaluate_answer(question, answer, job_title)
    return result
