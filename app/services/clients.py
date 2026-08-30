from __future__ import annotations

import re
from typing import TYPE_CHECKING
from uuid import UUID

from app.errors import NotFoundError
from app.models.client import Client
from app.models.enums import ClientType
from app.schemas.client import ClientCreate, ClientUpdate
from app.schemas.common import Page, Pagination

if TYPE_CHECKING:
    from app.api.deps import PaginationParams


async def create_client(payload: ClientCreate) -> Client:
    client = Client(**payload.model_dump(exclude_unset=False))
    await client.insert()
    return client


async def get_client(client_id: UUID) -> Client:
    client = await Client.get(client_id)
    if client is None:
        raise NotFoundError(f"Client {client_id} not found")
    return client


async def update_client(client_id: UUID, payload: ClientUpdate) -> Client:
    client = await get_client(client_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(client, key, value)
    await client.save()
    return client


async def list_clients(
    company_name: str | None,
    client_type: ClientType | None,
    region: str | None,
    pagination: PaginationParams,
) -> Page:
    query: dict = {}
    if company_name:
        query["companyName"] = {"$regex": re.escape(company_name), "$options": "i"}
    if client_type is not None:
        query["clientType"] = client_type.value
    if region:
        query["region"] = {"$regex": re.escape(region), "$options": "i"}

    total = await Client.find(query).count()
    docs = (
        await Client.find(query)
        .sort(("companyName", 1))
        .skip(pagination.skip)
        .limit(pagination.limit)
        .to_list()
    )
    pages = (total + pagination.size - 1) // pagination.size if pagination.size else 0
    return Page(
        items=docs,
        pagination=Pagination(
            page=pagination.page, size=pagination.size, total=total, pages=pages
        ),
    )
