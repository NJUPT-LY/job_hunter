from fastapi import APIRouter, HTTPException, Query, Body
from typing import Optional, List
from app.models.schemas import Job, JobPage, CrawlJobsRequest, ImportJobsRequest
from app.services.job_service import JobService
from app.core.config import settings
import asyncio

router = APIRouter()


@router.get("/", response_model=List[Job])
def list_jobs(
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    location: Optional[str] = Query(None, description="工作地点"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    jobs = JobService.list_jobs(keyword=keyword, location=location, page=page, page_size=page_size)
    return jobs


@router.get("/search", response_model=List[Job])
def search_jobs(keyword: str = Query(..., description="搜索关键词")):
    jobs = JobService.search_jobs(keyword)
    return jobs


@router.get("/export")
def export_jobs(
    keyword: Optional[str] = Query(None, description="可选的关键词过滤"),
    location: Optional[str] = Query(None, description="可选的位置过滤")
):
    """
    导出职位数据

    - 支持关键词和位置过滤
    - 返回JSON格式数据
    - 包含导出时间戳
    """
    try:
        result = JobService.export_jobs(keyword=keyword, location=location)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


@router.get("/cache/status")
def get_cache_status():
    """获取缓存状态信息"""
    return JobService.get_cache_status()


@router.get("/page", response_model=JobPage)
def list_jobs_page(
    keyword: Optional[str] = None, location: Optional[str] = None,
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
):
    return JobService.list_jobs_page(keyword, location, page, page_size)


@router.get("/stats")
def job_stats():
    return JobService.get_stats()


@router.get("/{job_id}", response_model=Job)
def get_job(job_id: str):
    job = JobService.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="职位不存在")
    return job


@router.post("/crawl")
async def crawl_jobs(request: CrawlJobsRequest):
    try:
        return await asyncio.wait_for(JobService.crawl_jobs(request.keyword), settings.CRAWL_TIMEOUT)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="职位获取超时，请稍后重试")


@router.post("/import")
def import_jobs(request: ImportJobsRequest):
    """
    导入职位数据

    - 自动验证数据格式
    - 基于ID和URL去重
    - 返回导入统计信息
    """
    try:
        result = JobService.import_jobs(request.jobs)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")
