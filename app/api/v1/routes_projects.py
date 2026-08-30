from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.deps import PaginationParams, ProjectFilterParams
from app.schemas.common import Page
from app.schemas.financials import ArrayMode, FinancialsPatch
from app.schemas.project import ProjectCreate, ProjectRead, ProjectSummary
from app.schemas.workflow import WorkflowPatch
from app.services import projects as projects_service

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectRead, status_code=201)
async def create_project(payload: ProjectCreate) -> ProjectRead:
    return await projects_service.create_project(payload)


@router.get("", response_model=Page[ProjectSummary])
async def list_projects(
    filters: ProjectFilterParams = Depends(),
    pagination: PaginationParams = Depends(),
) -> Page[ProjectSummary]:
    return await projects_service.list_projects(filters, pagination)


@router.get("/{project_id}", response_model=ProjectRead)
async def get_project(project_id: UUID) -> ProjectRead:
    return await projects_service.get_project(project_id)


@router.patch("/{project_id}/workflow", response_model=ProjectRead)
async def patch_workflow(project_id: UUID, payload: WorkflowPatch) -> ProjectRead:
    return await projects_service.patch_workflow(project_id, payload)


@router.patch("/{project_id}/financials", response_model=ProjectRead)
async def patch_financials(
    project_id: UUID,
    payload: FinancialsPatch,
    array_mode: ArrayMode = Query(ArrayMode.replace, alias="arrayMode"),
) -> ProjectRead:
    return await projects_service.patch_financials(project_id, payload, array_mode)
