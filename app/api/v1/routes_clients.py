from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.deps import PaginationParams
from app.models.enums import ClientType
from app.schemas.client import ClientCreate, ClientRead, ClientUpdate
from app.schemas.common import Page
from app.schemas.project import ProjectSummary
from app.services import clients as clients_service
from app.services import projects as projects_service

router = APIRouter(prefix="/clients", tags=["clients"])


@router.post("", response_model=ClientRead, status_code=201)
async def create_client(payload: ClientCreate) -> ClientRead:
    return await clients_service.create_client(payload)


@router.get("", response_model=Page[ClientRead])
async def list_clients(
    pagination: PaginationParams = Depends(),
    company_name: str | None = Query(None, alias="companyName"),
    client_type: ClientType | None = Query(None, alias="clientType"),
    region: str | None = Query(None),
) -> Page[ClientRead]:
    return await clients_service.list_clients(company_name, client_type, region, pagination)


@router.get("/{client_id}", response_model=ClientRead)
async def get_client(client_id: UUID) -> ClientRead:
    return await clients_service.get_client(client_id)


@router.patch("/{client_id}", response_model=ClientRead)
async def update_client(client_id: UUID, payload: ClientUpdate) -> ClientRead:
    return await clients_service.update_client(client_id, payload)


@router.get("/{client_id}/projects", response_model=Page[ProjectSummary])
async def list_client_projects(
    client_id: UUID, pagination: PaginationParams = Depends()
) -> Page[ProjectSummary]:
    return await projects_service.list_projects_for_client(client_id, pagination)
