import os
from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List


BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    PROJECT_NAME: str = "职路AI"
    VERSION: str = "0.1.0"
    API_PREFIX: str = "/api/v1"

    # --- 环境标识 ---
    ENVIRONMENT: str = "development"  # development / production
    DEBUG: bool = True
    SECRET_KEY: str = "dev-secret-key-change-in-production"

    # --- AI服务配置 ---
    AI_PROVIDER: str = "openai"  # openai / dashscope / zhipu
    AI_API_KEY: Optional[str] = None
    AI_API_BASE_URL: Optional[str] = None
    AI_MODEL: Optional[str] = None
    AI_TIMEOUT: int = 30
    CRAWL_TIMEOUT: int = 150

    # --- 数据存储 ---
    DATA_DIR: str = str(BACKEND_DIR / "data")
    LOG_DIR: str = str(BACKEND_DIR / "logs")

    # --- 日志配置 ---
    LOG_LEVEL: str = "INFO"  # DEBUG / INFO / WARNING / ERROR
    LOG_FORMAT: str = "text"  # text / json
    LOG_ROTATION_DAYS: int = 30

    # --- CORS 安全配置 ---
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    CORS_ALLOW_CREDENTIALS: bool = True

    # --- 速率限制 ---
    RATE_LIMIT_MAX_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    # --- 安全头 ---
    SECURITY_HEADERS_X_CONTENT_TYPE: bool = True
    SECURITY_HEADERS_X_FRAME_OPTIONS: str = "DENY"
    SECURITY_HEADERS_X_XSS_PROTECTION: bool = True

    @property
    def is_production(self) -> bool:
        """判断当前是否为生产环境"""
        return self.ENVIRONMENT.lower() == "production"

    @property
    def is_development(self) -> bool:
        """判断当前是否为开发环境"""
        return self.ENVIRONMENT.lower() == "development"

    model_config = SettingsConfigDict(env_file_encoding="utf-8")

    @field_validator("DATA_DIR", "LOG_DIR")
    @classmethod
    def resolve_directory(cls, value: str) -> str:
        path = Path(value).expanduser()
        return str(path if path.is_absolute() else BACKEND_DIR / path)


# 根据环境变量决定加载哪个配置文件
_env_file = BACKEND_DIR / ".env"
if os.environ.get("ENVIRONMENT") == "production":
    _env_file = BACKEND_DIR / ".env.production"

settings = Settings(_env_file=_env_file)
