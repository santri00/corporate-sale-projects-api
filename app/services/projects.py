from __future__ import annotations

import re
from datetime import datetime, time
from typing import TYPE_CHECKING
from uuid import UUID

from app.errors import NotFoundError, ValidationAppError
from app.models.client import Client
from app.models.project import Project
from app.schemas.common import Page, Pagination
from app.schemas.financials import ArrayMode, FinancialsPatch
from app.schemas.project import DateField, ProjectCreate, ProjectSummary
from app.schemas.workflow import WorkflowPatch
from app.services import workflow_rules

if TYPE_CHECKING:
    from app.api.deps import PaginationParams, ProjectFilterParams

_DATE_PATHS = {
    DateField.created_at: "createdAt",
    DateField.delivery_need_by_date: "workflow.deliveryNeedByDate",
    DateField.closed_at: "closedAt",
}
_DATETIME_FIELDS = {DateField.created_at, DateField.closed_at}

_SCALAR_FINANCIAL_FIELDS = (
    "budget",
    "total_sale",
    "billing_address",
    "payment_terms",
    "payment_collected_date",
    "project_close_date",
)
_ARRAY_FINANCIAL_FIELDS = ("quote_ids", "order_numbers")


# --------------------------------------------------------------------------- #
# Commands
# --------------------------------------------------------------------------- #
async def create_project(payload: ProjectCreate) -> Project:
    if await Client.get(payload.client_id) is None:
        raise ValidationAppError(f"Client {payload.client_id} does not exist")

    project = Project(**payload.model_dump(exclude_unset=False))
    workflow_rules.reconcile_on_create(project)
    await project.insert()
    return project


async def get_project(project_id: UUID) -> Project:
    project = await Project.get(project_id)
    if project is None:
        raise NotFoundError(f"Project {project_id} not found")
    return project


async def patch_workflow(project_id: UUID, payload: WorkflowPatch) -> Project:
    project = await get_project(project_id)
    workflow_rules.apply_workflow_update(project, payload)
    await project.save()
    return project


async def patch_financials(
    project_id: UUID, payload: FinancialsPatch, array_mode: ArrayMode
) -> Project:
    project = await get_project(project_id)
    _apply_financials_update(project, payload, array_mode)
    await project.save()
    return project


def _apply_financials_update(
    project: Project, patch: FinancialsPatch, array_mode: ArrayMode
) -> None:
    fin = project.financials
    provided = patch.model_dump(exclude_unset=True)

    for field in _SCALAR_FINANCIAL_FIELDS:
        if field in provided:
            setattr(fin, field, getattr(patch, field))

    for field in _ARRAY_FINANCIAL_FIELDS:
        if field not in provided:
            continue
        incoming = list(getattr(patch, field) or [])
        current = list(getattr(fin, field) or [])
        if array_mode == ArrayMode.replace:
            result = incoming
        elif array_mode == ArrayMode.append:
            result = current + [v for v in incoming if v not in current]
        else:  # remove
            drop = set(incoming)
            result = [v for v in current if v not in drop]
        setattr(fin, field, result)


# --------------------------------------------------------------------------- #
# Queries
# --------------------------------------------------------------------------- #
async def list_projects(
    filters: ProjectFilterParams, pagination: PaginationParams
) -> Page:
    query = await _build_query(filters)
    return await _paginated(query, [(filters.sort_field, filters.sort_dir)], pagination)


async def list_projects_for_client(
    client_id: UUID, pagination: PaginationParams
) -> Page:
    if await Client.get(client_id) is None:
        raise NotFoundError(f"Client {client_id} not found")
    return await _paginated({"clientId": client_id}, [("createdAt", -1)], pagination)


async def _paginated(
    query: dict, sort: list[tuple[str, int]], pagination: PaginationParams
) -> Page:
    total = await Project.find(query).count()
    docs = (
        await Project.find(query)
        .sort(*sort)
        .skip(pagination.skip)
        .limit(pagination.limit)
        .to_list()
    )
    items = await _to_summaries(docs)
    pages = (total + pagination.size - 1) // pagination.size if pagination.size else 0
    return Page(
        items=items,
        pagination=Pagination(
            page=pagination.page, size=pagination.size, total=total, pages=pages
        ),
    )


async def _to_summaries(docs: list[Project]) -> list[ProjectSummary]:
    client_ids = {d.client_id for d in docs}
    name_by_id: dict[UUID, str] = {}
    if client_ids:
        clients = await Client.find({"_id": {"$in": list(client_ids)}}).to_list()
        name_by_id = {c.id: c.company_name for c in clients}

    return [
        ProjectSummary(
            id=d.id,
            project_name=d.project_name,
            project_type=d.project_type,
            priority=d.priority,
            status=d.workflow.status,
            client_id=d.client_id,
            company_name=name_by_id.get(d.client_id),
            created_at=d.created_at,
            closed_at=d.closed_at,
        )
        for d in docs
    ]


async def _build_query(filters: ProjectFilterParams) -> dict:
    query: dict = {}

    id_set: set[UUID] | None = None
    if filters.client_id is not None:
        id_set = {filters.client_id}
    if filters.client_name:
        matched = await Client.find(
            {"companyName": {"$regex": re.escape(filters.client_name), "$options": "i"}}
        ).to_list()
        matched_ids = {c.id for c in matched}
        id_set = matched_ids if id_set is None else (id_set & matched_ids)
    if id_set is not None:
        query["clientId"] = {"$in": list(id_set)}

    if filters.status is not None:
        query["workflow.status"] = filters.status.value
    if filters.project_type is not None:
        query["projectType"] = filters.project_type.value
    if filters.priority is not None:
        query["priority"] = filters.priority.value

    date_query = _date_range(filters)
    if date_query is not None:
        query[_DATE_PATHS[filters.date_field]] = date_query

    return query


def _date_range(filters: ProjectFilterParams) -> dict | None:
    if not filters.date_from and not filters.date_to:
        return None

    # createdAt / closedAt are stored as datetimes; deliveryNeedByDate as an
    # ISO-8601 date string (Beanie serialises `datetime.date` that way). ISO
    # strings order lexicographically, so range comparisons still hold.
    is_datetime = filters.date_field in _DATETIME_FIELDS
    rng: dict = {}
    if filters.date_from:
        rng["$gte"] = (
            datetime.combine(filters.date_from, time.min)
            if is_datetime
            else filters.date_from.isoformat()
        )
    if filters.date_to:
        rng["$lte"] = (
            datetime.combine(filters.date_to, time.max)
            if is_datetime
            else filters.date_to.isoformat()
        )
    return rng
