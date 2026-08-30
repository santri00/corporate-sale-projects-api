from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

from pydantic import Field

from app.models.common import CamelModel
from app.models.enums import Priority, ProjectType, Sector, WorkflowState
from app.models.project import (
    CorporateGifting,
    DesignServices,
    Financials,
    LogisticsAndDelivery,
    TeamAssignment,
    Triggers,
    WorkflowStatus,
)


class DateField(StrEnum):
    """Selects which project date the ``GET /projects`` range filter applies to."""

    created_at = "createdAt"
    delivery_need_by_date = "deliveryNeedByDate"
    closed_at = "closedAt"


class WorkflowCreate(CamelModel):
    status: WorkflowState = WorkflowState.NEW
    delivery_need_by_date: date | None = None
    triggers: Triggers = Field(default_factory=Triggers)


class ProjectCreate(CamelModel):
    client_id: UUID
    project_name: str
    description: str | None = None
    project_type: ProjectType
    sector: Sector | None = None
    product_scope: str | None = None
    priority: Priority | None = None
    notes: str | None = None

    workflow: WorkflowCreate = Field(default_factory=WorkflowCreate)
    team: TeamAssignment = Field(default_factory=TeamAssignment)
    financials: Financials = Field(default_factory=Financials)
    logistics: LogisticsAndDelivery = Field(default_factory=LogisticsAndDelivery)
    design_services: DesignServices | None = None
    corporate_gifting: CorporateGifting | None = None


class ProjectRead(CamelModel):
    id: UUID
    created_at: datetime
    client_id: UUID
    project_name: str
    description: str | None = None
    project_type: ProjectType
    sector: Sector | None = None
    product_scope: str | None = None
    priority: Priority | None = None
    notes: str | None = None
    closed_at: datetime | None = None

    workflow: WorkflowStatus
    team: TeamAssignment
    financials: Financials
    logistics: LogisticsAndDelivery
    design_services: DesignServices | None = None
    corporate_gifting: CorporateGifting | None = None


class ProjectSummary(CamelModel):
    id: UUID
    project_name: str
    project_type: ProjectType
    priority: Priority | None = None
    status: WorkflowState
    client_id: UUID
    company_name: str | None = None
    created_at: datetime
    closed_at: datetime | None = None
