"""
AI服务API端点 - 健康检查、调用日志查询
"""

from fastapi import APIRouter
from app.services.ai_service import health_check, get_call_log
from app.core.response import success_response

router = APIRouter()


@router.get("/health")
async def ai_health_check():
    """AI服务健康检查"""
    result = await health_check()
    return success_response(data=result)


@router.get("/logs")
async def ai_call_logs():
    """获取AI调用日志"""
    logs = get_call_log()
    return success_response(data={"logs": logs, "total": len(logs)})
