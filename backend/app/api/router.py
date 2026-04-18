from fastapi import APIRouter
from app.api import jobs, analysis, action_plan, resume, interview

router = APIRouter()

router.include_router(jobs.router, prefix="/jobs", tags=["职位"])
router.include_router(analysis.router, prefix="/analysis", tags=["分析"])
router.include_router(action_plan.router, prefix="/action-plan", tags=["行动清单"])
router.include_router(resume.router, prefix="/resume", tags=["简历"])
router.include_router(interview.router, prefix="/interview", tags=["面试"])
