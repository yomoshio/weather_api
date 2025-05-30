import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from tortoise import Tortoise
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.core.database import TORTOISE_ORM, init_db, close_db
from app.api.v1.routes import router as api_router


@asynccontextmanager
async def lifespan(app: FastAPI):    
    await init_db()
    yield
    await close_db()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Weather Forecast App",
        version="1.0.0",
        lifespan=lifespan
    )
    

    app.mount("/static", StaticFiles(directory="app/static"), name="static")
    
    app.include_router(api_router, prefix="/api/v1")
    
    return app



app = create_app()


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)