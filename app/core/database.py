from tortoise import Tortoise
from .config import settings

TORTOISE_ORM = {
    "connections": {
        "default": {
            "engine": "tortoise.backends.asyncpg",
            "credentials": {
                "host": "localhost",      
                "port": 5432,      
                "user": settings.DATABASE_USER,      
                "password": settings.DATABASE_PASSWORD,
                "database": settings.DATABASE_NAME,
            }
        }
    },
    "apps": {
        "models": {
            "models": ["app.models.models", "aerich.models"],
            "default_connection": "default",
        }
    }
}

async def init_db():
    """Инициализация базы данных"""
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas()

async def close_db():
    """Закрытие соединения с базой"""
    await Tortoise.close_connections()