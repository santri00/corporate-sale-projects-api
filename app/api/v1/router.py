from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.routes_clients import router as clients_router
from app.api.v1.routes_projects import router as projects_router
from app.core.config import settings

api_router = APIRouter(prefix=settings.api_base_path)


@api_router.get("/health", tags=["meta"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


api_router.include_router(clients_router)
api_router.include_router(projects_router)
