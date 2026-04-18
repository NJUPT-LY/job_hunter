from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "职路AI"
    VERSION: str = "0.1.0"
    API_PREFIX: str = "/api/v1"
    
    AI_API_KEY: Optional[str] = None
    AI_API_BASE_URL: Optional[str] = "https://api.openai.com/v1"
    AI_MODEL: str = "gpt-3.5-turbo"
    
    DATA_DIR: str = "./data"
    
    class Config:
        env_file = ".env"


settings = Settings()
