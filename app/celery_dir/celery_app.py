from celery import Celery
from app.core.config import settings


celery_app = Celery(
    "weather-app",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.celery_dir.tasks"]
)


celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    result_expires=3600,  
)