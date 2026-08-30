from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.db import init_database
from app.errors import register_error_handlers


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await init_database()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Corporate Sales Projects API",
        version="1.0.0",
        lifespan=lifespan,
    )
    register_error_handlers(app)
    app.include_router(api_router)
    return app


app = create_app()
