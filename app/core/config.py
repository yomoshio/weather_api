
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_USER: str = os.getenv("DATABASE_USER", "")
    DATABASE_PASSWORD: str = os.getenv("DATABASE_PASSWORD", "")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "")
    WEATHER_API_KEY: str = os.getenv("WEATHER_API_KEY", "")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    class Config:
        env_file = ".env"


settings = Settings()
