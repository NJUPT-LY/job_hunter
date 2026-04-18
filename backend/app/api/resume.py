from typing import List, Optional
from fastapi import APIRouter
from app.models.schemas import ResumeTemplate
from app.services.resume_service import ResumeService

router = APIRouter()


@router.get("/templates", response_model=List[ResumeTemplate])
async def get_templates(category: Optional[str] = None):
    templates = ResumeService.get_templates(category)
    return templates


@router.post("/evaluate")
async def evaluate_resume(resume_content: str, target_job: str):
    result = await ResumeService.evaluate_resume(resume_content, target_job)
    return result


@router.post("/optimize")
async def optimize_resume(resume_content: str, target_job: str):
    result = await ResumeService.optimize_resume(resume_content, target_job)
    return result
