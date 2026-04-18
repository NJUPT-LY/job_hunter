from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from app.models.schemas import Job
from app.services.job_service import JobService

router = APIRouter()


@router.get("/", response_model=List[Job])
async def list_jobs(
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    location: Optional[str] = Query(None, description="工作地点"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    jobs = JobService.list_jobs(keyword=keyword, location=location, page=page, page_size=page_size)
    return jobs


@router.get("/search", response_model=List[Job])
async def search_jobs(keyword: str = Query(..., description="搜索关键词")):
    jobs = JobService.search_jobs(keyword)
    return jobs


@router.get("/{job_id}", response_model=Job)
async def get_job(job_id: str):
    job = JobService.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="职位不存在")
    return job


@router.post("/crawl")
async def crawl_jobs(keyword: str = Query(..., description="搜索关键词")):
    result = await JobService.crawl_jobs(keyword)
    return result
