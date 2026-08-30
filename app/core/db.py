"""MongoDB / Beanie initialisation.

`init_database` is called once on application startup (see ``app.main.lifespan``).
Tests call it directly with an in-process ``mongomock_motor`` client so no real
MongoDB server is required.
"""

from __future__ import annotations

from typing import Any

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings
from app.models.client import Client
from app.models.project import Project

DOCUMENT_MODELS = [Client, Project]

_client: AsyncIOMotorClient | None = None


def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(settings.mongo_uri, uuidRepresentation="standard")
    return _client


async def init_database(client: Any | None = None) -> None:
    """Bind the Beanie document models to a database.

    Parameters
    ----------
    client:
        Optional Motor-compatible client. When omitted a real
        ``AsyncIOMotorClient`` is created from settings.
    """

    db_client = client if client is not None else get_client()
    await init_beanie(database=db_client[settings.mongo_db], document_models=DOCUMENT_MODELS)
