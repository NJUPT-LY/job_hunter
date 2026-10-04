import time
import logging
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.router import router as api_router
from app.core.config import settings
from app.core.response import ResponseCode, error_response
from app.core.logging_config import setup_logging


# ============================================================
# 初始化日志系统
# ============================================================
setup_logging(
    env=settings.ENVIRONMENT,
    log_level=settings.LOG_LEVEL,
    log_format=settings.LOG_FORMAT,
    log_dir=settings.LOG_DIR,
    rotation_days=settings.LOG_ROTATION_DAYS,
)

logger = logging.getLogger("zhilu_api")

# ============================================================
# 中间件定义
# ============================================================


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    速率限制中间件
    基于IP地址限制请求频率, 防止API滥用
    """

    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: dict = {}  # {ip: [(timestamp, count)]}

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"

        # 健康检查和静态资源不限流
        if request.url.path in ("/health", "/ready", "/docs", "/redoc", "/openapi.json"):
            return await call_next(request)

        now = time.monotonic()
        window_start = now - self.window_seconds

        # 删除已经过期的访客，避免长期运行时 IP 记录无限增长。
        if not hasattr(self, "last_cleanup") or now - self.last_cleanup >= self.window_seconds:
            self.requests = {ip: [t for t in timestamps if t > window_start]
                             for ip, timestamps in self.requests.items()
                             if timestamps and timestamps[-1] > window_start}
            self.last_cleanup = now

        # 清理过期记录
        if client_ip in self.requests:
            self.requests[client_ip] = [
                t for t in self.requests[client_ip] if t > window_start
            ]

        # 检查是否超出限制
        current_count = len(self.requests.get(client_ip, []))
        if current_count >= self.max_requests:
            logger.warning(
                "速率限制触发: IP=%s, 请求数=%d/%d, 路径=%s",
                client_ip, current_count, self.max_requests, request.url.path
            )
            return JSONResponse(
                status_code=429,
                content=error_response(
                    message="请求过于频繁，请稍后重试",
                    code=ResponseCode.RATE_LIMIT_EXCEEDED,
                ),
                headers={"Retry-After": str(self.window_seconds)},
            )

        # 记录请求
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        self.requests[client_ip].append(now)

        response = await call_next(request)
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    安全请求头中间件
    添加常见安全响应头, 防御常见Web攻击
    """

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # X-Content-Type-Options: 防止MIME类型嗅探
        if settings.SECURITY_HEADERS_X_CONTENT_TYPE:
            response.headers["X-Content-Type-Options"] = "nosniff"

        # X-Frame-Options: 防止点击劫持
        response.headers["X-Frame-Options"] = settings.SECURITY_HEADERS_X_FRAME_OPTIONS

        # X-XSS-Protection: XSS防护
        if settings.SECURITY_HEADERS_X_XSS_PROTECTION:
            response.headers["X-XSS-Protection"] = "1; mode=block"

        # Strict-Transport-Security: 强制HTTPS (仅生产环境)
        if settings.is_production:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        # 移除Server头, 避免暴露服务器信息
        if "server" in response.headers:
            del response.headers["server"]

        return response


class RequestIdMiddleware(BaseHTTPMiddleware):
    """
    请求ID中间件
    为每个请求生成唯一ID, 便于日志追踪
    """

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        # 将request_id注入到请求状态中, 供日志使用
        request.state.request_id = request_id

        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time

        # 在响应头中返回request_id
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{process_time:.4f}"

        # 记录请求日志
        logger.info(
            "%s %s - 状态: %s, 耗时: %.4fs",
            request.method,
            request.url.path,
            response.status_code,
            process_time,
        )

        return response


# ============================================================
# 应用工厂
# ============================================================

# 记录服务启动时间
_startup_time = datetime.utcnow()


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(app):
        Path(settings.DATA_DIR).mkdir(parents=True, exist_ok=True)
        yield

    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description="职路AI - 大学生求职导航平台API",
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        lifespan=lifespan,
    )

    # --- CORS 中间件 ---
    # 生产环境从环境变量读取允许的域名, 开发环境保留宽松配置
    cors_origins = settings.CORS_ORIGINS
    if settings.is_development:
        # 开发环境: 保留localhost访问
        cors_origins = list(set(cors_origins + [
            "http://localhost:5173",
            "http://localhost:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:3000",
        ]))

    # --- 安全中间件 ---
    app.add_middleware(SecurityHeadersMiddleware)

    # --- 请求ID中间件 ---
    app.add_middleware(RequestIdMiddleware)

    # --- 速率限制中间件 ---
    app.add_middleware(
        RateLimitMiddleware,
        max_requests=settings.RATE_LIMIT_MAX_REQUESTS,
        window_seconds=settings.RATE_LIMIT_WINDOW_SECONDS,
    )

    # CORS 放在最外层，限流响应也需携带跨域响应头。
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "Accept", "X-Requested-With"],
        max_age=3600,
    )

    # --- 异常处理 ---

    # HTTP异常处理 - 处理404、405等FastAPI/Starlette抛出的HTTP异常
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        logger.warning(
            "HTTP异常: %s %s - 状态码: %s, 详情: %s",
            request.method, request.url.path, exc.status_code, exc.detail
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response(
                message=str(exc.detail),
                code=exc.status_code
            )
        )

    # 请求验证异常处理 - 处理Pydantic验证错误
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.warning(
            "验证错误: %s %s - 错误数量: %s",
            request.method, request.url.path, len(exc.errors())
        )
        errors_detail = []
        for error in exc.errors():
            field = " -> ".join(str(loc) for loc in error.get("loc", []))
            msg = error.get("msg", "")
            errors_detail.append(f"{field}: {msg}")
        return JSONResponse(
            status_code=422,
            content=error_response(
                message="请求参数验证失败",
                code=ResponseCode.VALIDATION_ERROR,
                data={"errors": errors_detail}
            )
        )

    # 通用HTTPException处理
    @app.exception_handler(HTTPException)
    async def fastapi_http_exception_handler(request: Request, exc: HTTPException):
        logger.warning(
            "业务异常: %s %s - 状态码: %s, 详情: %s",
            request.method, request.url.path, exc.status_code, exc.detail
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response(
                message=str(exc.detail),
                code=exc.status_code
            )
        )

    # 全局未捕获异常处理
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(
            "未捕获异常: %s %s - 异常类型: %s, 详情: %s",
            request.method, request.url.path, type(exc).__name__, str(exc),
            exc_info=True
        )
        return JSONResponse(
            status_code=500,
            content=error_response(
                message="服务器内部错误，请稍后重试",
                code=ResponseCode.INTERNAL_ERROR
            )
        )

    # --- 注册路由 ---
    app.include_router(api_router, prefix=settings.API_PREFIX)

    # --- 健康检查端点 ---

    @app.get("/health")
    async def health_check():
        """基础健康检查 - 用于负载均衡器探测"""
        uptime = (datetime.utcnow() - _startup_time).total_seconds()
        return {
            "status": "ok",
            "message": "职路AI服务运行中",
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
            "uptime_seconds": round(uptime, 2),
        }

    @app.get("/ready")
    async def readiness_check():
        """就绪探针 - 用于K8s readiness probe"""
        try:
            # 检查数据目录是否可访问
            import os
            data_dir_ok = os.path.isdir(settings.DATA_DIR)

            return JSONResponse(status_code=200 if data_dir_ok else 503, content={
                "status": "ready" if data_dir_ok else "not_ready",
                "checks": {
                    "data_directory": "ok" if data_dir_ok else "error",
                },
            })
        except Exception as e:
            logger.error("就绪检查失败: %s", str(e))
            return JSONResponse(
                status_code=503,
                content={
                    "status": "not_ready",
                    "error": str(e),
                },
            )

    @app.get(f"{settings.API_PREFIX}/health/detailed")
    async def detailed_health_check():
        """详细健康检查 - 用于监控系统"""
        uptime = (datetime.utcnow() - _startup_time).total_seconds()

        # AI服务状态
        from app.services.ai_service import get_provider_config, is_api_key_configured
        config = get_provider_config()
        ai_status = "configured" if is_api_key_configured(settings.AI_API_KEY) else "not_configured"
        ai_provider = config["provider"]

        # 数据目录状态
        import os
        data_dir = settings.DATA_DIR
        data_exists = os.path.isdir(data_dir)
        data_files = []
        if data_exists:
            try:
                data_files = [
                    f for f in os.listdir(data_dir) if f.endswith(".json")
                ]
            except Exception:
                pass

        return {
            "status": "healthy",
            "service": {
                "name": settings.PROJECT_NAME,
                "version": settings.VERSION,
                "environment": settings.ENVIRONMENT,
                "debug": settings.DEBUG,
            },
            "uptime": {
                "seconds": round(uptime, 2),
                "started_at": _startup_time.isoformat(),
            },
            "ai_service": {
                "status": ai_status,
                "provider": ai_provider,
                "model": config["model"],
                "base_url": config["base_url"],
            },
            "data": {
                "directory": data_dir,
                "accessible": data_exists,
                "files": data_files,
                "file_count": len(data_files),
            },
            "cache": {
                "status": "enabled",
                "ttl_seconds": 60,
            },
        }

    logger.info("职路AI服务启动完成 - 版本: %s, 环境: %s", settings.VERSION, settings.ENVIRONMENT)
    return app


app = create_app()
