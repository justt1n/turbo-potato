from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes.app_routes import router as app_router
from app.api.routes.health import router as health_router
from app.core.config import get_settings
from app.core.dependencies import get_bootstrapper


@asynccontextmanager
async def lifespan(_: FastAPI):
    get_bootstrapper().bootstrap()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Turbo Potato Backend",
        version="0.1.0",
        debug=settings.app.env == "development",
        lifespan=lifespan,
    )
    app.include_router(health_router, prefix="/api/v1")
    app.include_router(app_router, prefix="/api/v1")

    return app


app = create_app()
