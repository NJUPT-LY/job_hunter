from fastapi import APIRouter, HTTPException
from app.models.schemas import JobAnalysis, SkillGap
from app.services.analyzer import JobAnalyzer

router = APIRouter()


@router.post("/analyze/{job_id}", response_model=JobAnalysis)
async def analyze_job(job_id: str):
    analysis = JobAnalyzer.analyze_job(job_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="分析失败")
    return analysis


@router.post("/gap", response_model=SkillGap)
async def analyze_skill_gap(user_skills: dict, job_id: str):
    gap = JobAnalyzer.analyze_skill_gap(user_skills, job_id)
    return gap


@router.post("/parse-jd")
async def parse_job_description(jd_text: str):
    result = await JobAnalyzer.parse_jd(jd_text)
    return result
