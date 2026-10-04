import sys

from app.core.config import settings

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        # Windows 重载模式会切换到不支持 Playwright 子进程的事件循环。
        reload=settings.is_development and sys.platform != "win32",
        workers=1,
    )
