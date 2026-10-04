"""
统一API响应格式模块

提供标准化的API响应结构：
{
    "code": int,        # 业务状态码
    "message": str,     # 提示信息
    "data": any,        # 响应数据
    "success": bool     # 是否成功
}
"""

from typing import Any, Optional
from fastapi.responses import JSONResponse


# 业务状态码定义
class ResponseCode:
    SUCCESS = 200           # 成功
    BAD_REQUEST = 400       # 请求参数错误
    UNAUTHORIZED = 401      # 未授权
    FORBIDDEN = 403         # 禁止访问
    NOT_FOUND = 404         # 资源不存在
    VALIDATION_ERROR = 422  # 数据验证错误
    INTERNAL_ERROR = 500    # 服务器内部错误
    SERVICE_UNAVAILABLE = 503  # 服务不可用
    RATE_LIMIT_EXCEEDED = 429  # 请求频率超限


def success_response(
    data: Any = None,
    message: str = "操作成功",
    code: int = ResponseCode.SUCCESS
) -> dict:
    """成功响应辅助函数"""
    return {
        "code": code,
        "message": message,
        "data": data,
        "success": True
    }


def error_response(
    message: str = "操作失败",
    code: int = ResponseCode.INTERNAL_ERROR,
    data: Any = None
) -> dict:
    """错误响应辅助函数"""
    return {
        "code": code,
        "message": message,
        "data": data,
        "success": False
    }


def json_success_response(
    data: Any = None,
    message: str = "操作成功",
    code: int = ResponseCode.SUCCESS,
    status_code: int = 200
) -> JSONResponse:
    """返回JSON格式的成功响应"""
    return JSONResponse(
        status_code=status_code,
        content=success_response(data=data, message=message, code=code)
    )


def json_error_response(
    message: str = "操作失败",
    code: int = ResponseCode.INTERNAL_ERROR,
    data: Any = None,
    status_code: int = 500
) -> JSONResponse:
    """返回JSON格式的错误响应"""
    return JSONResponse(
        status_code=status_code,
        content=error_response(message=message, code=code, data=data)
    )
