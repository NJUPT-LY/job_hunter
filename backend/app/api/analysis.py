from fastapi import APIRouter, HTTPException
from app.models.schemas import JobAnalysis, SkillGap, SkillGapRequest, ParseJDRequest
from app.services.analyzer import JobAnalyzer

router = APIRouter()


@router.post("/analyze/{job_id}", response_model=JobAnalysis)
def analyze_job(job_id: str):
    analysis = JobAnalyzer.analyze_job(job_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="分析失败")
    return analysis


@router.post("/gap", response_model=SkillGap)
def analyze_skill_gap(request: SkillGapRequest):
    if JobAnalyzer.analyze_job(request.job_id) is None:
        raise HTTPException(status_code=404, detail="职位不存在")
    gap = JobAnalyzer.analyze_skill_gap(request.user_skills, request.job_id)
    return gap


@router.post("/parse-jd")
async def parse_job_description(request: ParseJDRequest):
    result = await JobAnalyzer.parse_jd(request.jd_text)
    return result
