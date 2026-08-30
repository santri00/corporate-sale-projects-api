from __future__ import annotations

import mongomock.database
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from mongomock_motor import AsyncMongoMockClient

from app.core.db import init_database
from app.main import create_app

# Beanie >= 2 calls ``list_collection_names(authorizedCollections=True, nameOnly=True)``;
# mongomock's implementation doesn't accept those kwargs. Swallow the extras so the
# in-process mock stays usable for tests.
_orig_list_collection_names = mongomock.database.Database.list_collection_names


def _list_collection_names(self, filter=None, session=None, **_ignored):  # noqa: A002
    return _orig_list_collection_names(self, filter=filter, session=session)


mongomock.database.Database.list_collection_names = _list_collection_names

BASE = "/corporate-sales/v1"

CLIENT_PAYLOAD = {
    "companyName": "Acme Corp",
    "clientType": "DEVELOPER",
    "industry": "Real Estate",
    "region": "US-West",
    "address": {
        "line1": "1 Main St",
        "city": "San Francisco",
        "state": "CA",
        "postalCode": "94105",
        "country": "USA",
    },
    "pointOfContact": {"name": "Jane Doe", "email": "jane@acme.com", "phone": "555-1000"},
    "paymentTerms": "NET_30",
    "isFirstTimeClient": True,
}


def project_payload(client_id: str, **overrides) -> dict:
    payload = {
        "clientId": client_id,
        "projectName": "HQ Refresh",
        "projectType": "GENERAL_B2B",
        "sector": "COMMERCIAL",
        "priority": "HIGH",
        "description": "Office furniture package",
    }
    payload.update(overrides)
    return payload


@pytest_asyncio.fixture
async def api():
    # Fresh in-process Mongo per test => full isolation.
    await init_database(client=AsyncMongoMockClient())
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


@pytest_asyncio.fixture
async def client_id(api) -> str:
    resp = await api.post(f"{BASE}/clients", json=CLIENT_PAYLOAD)
    return resp.json()["id"]
