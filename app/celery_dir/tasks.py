import asyncio
from datetime import datetime
from tortoise import Tortoise

from .celery_app import celery_app
from app.api.v1.services.weather_service import WeatherService
from app.core.database import TORTOISE_ORM
from app.models.models import SearchHistory


@celery_app.task
def get_weather_async(city: str, user_id: str):
    """Асинхронная задача получения погоды"""
    return asyncio.run(_get_weather_task(city, user_id))


async def _get_weather_task(city: str, user_id: str):
    """Внутренняя асинхронная функция для получения погоды"""
    try:
        await Tortoise.init(config=TORTOISE_ORM)
        
        weather_service = WeatherService()
        weather_data = await weather_service.get_weather_by_city(city)
        
        # Добавляем отладочную информацию
        print(f"Weather data structure: {weather_data}")
        print(f"Available top-level keys: {list(weather_data.keys())}")
        
        # ИСПРАВЛЕНИЕ: Правильный путь к температуре
        # Было: temperature=weather_data["temperature"]
        # Стало: temperature=weather_data["current"]["temperature"]
        temperature = weather_data["current"]["temperature"]
        
        await SearchHistory.create(
            user_id=user_id,
            city=weather_data["city"],
            temperature=temperature,  # Используем извлеченную температуру
            timestamp=datetime.utcnow()
        )
        
        weather_data["timestamp"] = datetime.now().isoformat()
        
        return weather_data
        
    except KeyError as e:
        print(f"KeyError in _get_weather_task: {e}")
        if 'weather_data' in locals():
            print(f"Available keys in weather_data: {list(weather_data.keys())}")
            if 'current' in weather_data:
                print(f"Available keys in current: {list(weather_data['current'].keys())}")
        return {"error": f"Missing key: {str(e)}"}
    except Exception as e:
        print(f"Error in _get_weather_task: {e}")
        return {"error": str(e)}
    finally:
        await Tortoise.close_connections()


@celery_app.task
def cleanup_old_searches():
    """Задача для очистки старых записей поиска"""
    return asyncio.run(_cleanup_old_searches_task())


async def _cleanup_old_searches_task():
    """Удаление записей старше 30 дней"""
    try:
        await Tortoise.init(config=TORTOISE_ORM)
        
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        deleted_count = await SearchHistory.filter(
            timestamp__lt=cutoff_date
        ).delete()
        
        return {"deleted_count": deleted_count}
        
    except Exception as e:
        print(f"Error in _cleanup_old_searches_task: {e}")
        return {"error": str(e)}
    finally:
        await Tortoise.close_connections()