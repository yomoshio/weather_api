from fastapi import APIRouter, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from typing import List
import uuid
import asyncio
from datetime import datetime

from app.models.models import SearchHistory
from .schemas import (
    WeatherRequest, WeatherResponse, CitySuggestionsResponse,
    UserHistoryResponse, SearchStatsResponse, HealthResponse
)
from .services.weather_service import WeatherService
from app.celery_dir.tasks import get_weather_async

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")
weather_service = WeatherService()


async def wait_for_celery_task(task, timeout=30):
    """Асинхронное ожидание Celery задачи"""
    max_iterations = timeout * 10  # Проверяем каждые 100мс
    
    for _ in range(max_iterations):
        if task.ready():
            if task.successful():
                return task.result
            else:
                # Если задача завершилась с ошибкой
                raise Exception(f"Task failed: {task.info}")
        
        # Асинхронная пауза 100мс
        await asyncio.sleep(0.1)
    
    # Если таймаут превышен
    raise Exception("Task timeout exceeded")


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def home(request: Request):
    """Главная страница"""
    user_id = request.cookies.get("user_id")
    recent_cities = []
    
    if user_id:
        recent_searches = await SearchHistory.filter(
            user_id=user_id
        ).order_by("-timestamp").limit(5)
        recent_cities = [search.city for search in recent_searches]
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "recent_cities": recent_cities
    })


@router.get("/cities/suggestions", response_model=CitySuggestionsResponse)
async def get_city_suggestions(q: str):
    """Автодополнение городов"""
    try:
        suggestions = await weather_service.search_cities(q)
        return CitySuggestionsResponse(suggestions=suggestions)
    except Exception as e:
        print(f"Error in city suggestions: {e}")  # Добавляем логирование
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/weather", response_model=WeatherResponse)
async def get_weather(request: Request, weather_request: WeatherRequest):
    """Получение прогноза погоды"""
    try:
        user_id = request.cookies.get("user_id")
        if not user_id:
            user_id = str(uuid.uuid4())
        
        print(f"Starting weather task for city: {weather_request.city}, user: {user_id}")
        
        # Запускаем Celery задачу
        task = get_weather_async.delay(weather_request.city, user_id)
        print(f"Task ID: {task.id}")
        
        # Асинхронно ожидаем результат
        result = await wait_for_celery_task(task, timeout=30)
        
        print(f"Task completed with result: {result}")
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        
        response = JSONResponse(content=result)
        response.set_cookie(key="user_id", value=user_id, max_age=30*24*3600)
        
        return response
    
    except asyncio.TimeoutError:
        raise HTTPException(status_code=408, detail="Request timeout - weather service is taking too long")
    except Exception as e:
        print(f"Error in get_weather: {e}")  # Добавляем логирование
        raise HTTPException(status_code=500, detail=str(e))


# Альтернативный подход с разделением на два запроса
@router.post("/weather/start")
async def start_weather_task(request: Request, weather_request: WeatherRequest):
    """Запуск задачи получения погоды (возвращает task_id)"""
    try:
        user_id = request.cookies.get("user_id")
        if not user_id:
            user_id = str(uuid.uuid4())
        
        task = get_weather_async.delay(weather_request.city, user_id)
        
        response = JSONResponse(content={"task_id": task.id})
        response.set_cookie(key="user_id", value=user_id, max_age=30*24*3600)
        
        return response
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/weather/{city}", response_model=WeatherResponse)
async def get_weather_by_city(city: str, request: Request):
    """Получение прогноза погоды по названию города (GET запрос)"""
    try:
        user_id = request.cookies.get("user_id")
        if not user_id:
            user_id = str(uuid.uuid4())
        
        print(f"Starting weather task for city: {city}, user: {user_id}")
        
        # Запускаем Celery задачу
        task = get_weather_async.delay(city, user_id)
        print(f"Task ID: {task.id}")
        
        # Асинхронно ожидаем результат
        result = await wait_for_celery_task(task, timeout=30)
        
        print(f"Task completed with result: {result}")
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        
        response = JSONResponse(content=result)
        response.set_cookie(key="user_id", value=user_id, max_age=30*24*3600)
        
        return response
    
    except asyncio.TimeoutError:
        raise HTTPException(status_code=408, detail="Request timeout - weather service is taking too long")
    except Exception as e:
        print(f"Error in get_weather_by_city: {e}")  # Добавляем логирование
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=SearchStatsResponse)
async def get_search_stats():
    """Статистика поиска городов"""
    try:
        from tortoise import connections
        
        # Получаем соединение с базой данных
        conn = connections.get("default")
        
        # Выполняем raw запрос
        result = await conn.execute_query_dict(
            """
            SELECT city, COUNT(*) as count 
            FROM search_history 
            GROUP BY city 
            ORDER BY count DESC 
            LIMIT 20
            """
        )
        
        # Теперь result это список словарей
        stats_data = [{"city": row["city"], "count": row["count"]} for row in result]
        
        return SearchStatsResponse(stats=stats_data)
        
    except Exception as e:
        print(f"Error in get_search_stats: {e}")  # Добавляем логирование
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/history", response_model=UserHistoryResponse)
async def get_user_history(request: Request):
    """История поиска пользователя"""
    user_id = request.cookies.get("user_id")
    if not user_id:
        return UserHistoryResponse(history=[])
    
    try:
        history = await SearchHistory.filter(
            user_id=user_id
        ).order_by("-timestamp").limit(50)
        
        result = [
            {
                "city": h.city,
                "timestamp": h.timestamp,
                "temperature": h.temperature
            }
            for h in history
        ]
        
        return UserHistoryResponse(history=result)
    
    except Exception as e:
        print(f"Error in get_user_history: {e}")  # Добавляем логирование
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Проверка здоровья приложения"""
    return HealthResponse(
        status="healthy", 
        timestamp=datetime.now()
    )



@router.get("/task-status/{task_id}")
async def get_task_status(task_id: str):
    """Получение статуса Celery задачи"""
    try:
        from celery.result import AsyncResult
        
        result = AsyncResult(task_id)
        
        if result.ready():
            if result.successful():
                return {
                    "status": "SUCCESS",
                    "result": result.result
                }
            else:
                return {
                    "status": "FAILURE",
                    "error": str(result.info)
                }
        else:
            return {
                "status": "PENDING"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))