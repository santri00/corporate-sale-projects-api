from __future__ import annotations

from datetime import date, datetime
from uuid import UUID, uuid4

from beanie import Document
from pydantic import ConfigDict, Field

from app.models.common import Address, CamelModel, Contact, document_alias, utcnow
from app.models.enums import DeliveryType, Priority, ProjectType, Sector, WorkflowState


# --------------------------------------------------------------------------- #
# Embedded sub-documents
# --------------------------------------------------------------------------- #
class Triggers(CamelModel):
    is_quote_requested: bool = False
    is_product_finalized: bool = False
    is_split_requested: bool = False
    requires_design_services: bool = False


class WorkflowStatus(CamelModel):
    status: WorkflowState = WorkflowState.NEW
    held_from: WorkflowState | None = None
    delivery_need_by_date: date | None = None
    triggers: Triggers = Field(default_factory=Triggers)


class TeamAssignment(CamelModel):
    sales_lead: str | None = None
    designer: str | None = None
    artist_3d: str | None = Field(default=None, alias="artist3D")
    customer_care_lead: str | None = None
    merch_lead: str | None = None


class Financials(CamelModel):
    budget: float | None = None
    total_sale: float | None = None
    quote_ids: list[str] = Field(default_factory=list)
    order_numbers: list[str] = Field(default_factory=list)
    billing_address: Address | None = None
    payment_terms: str | None = None
    payment_collected_date: date | None = None
    project_close_date: date | None = None


class DeliveryRequirements(CamelModel):
    palletization: bool = False
    full_install: bool = False
    has_loading_dock: bool = False
    lift_gate: bool = False
    pallet_jack: bool = False
    driver_assist: bool = False


class LogisticsAndDelivery(CamelModel):
    delivery_type: DeliveryType | None = None
    delivery_address: Address | None = None
    receiving_contact: Contact | None = None
    receiving_hours: str | None = None
    requirements: DeliveryRequirements = Field(default_factory=DeliveryRequirements)
    max_equipment_size: str | None = None


class DesignServices(CamelModel):
    design_package_id: UUID | None = None


class GiftMessage(CamelModel):
    message_type: str | None = None
    content: str | None = None


class Personalization(CamelModel):
    is_personalized: bool = False
    personalization_details: str | None = None


class CorporateGifting(CamelModel):
    gift_message: GiftMessage = Field(default_factory=GiftMessage)
    personalization: Personalization = Field(default_factory=Personalization)
    is_gift_boxed: bool = False


# --------------------------------------------------------------------------- #
# Aggregate root
# --------------------------------------------------------------------------- #
class Project(Document):
    model_config = ConfigDict(alias_generator=document_alias, populate_by_name=True)

    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=utcnow)

    client_id: UUID
    project_name: str
    description: str | None = None
    project_type: ProjectType
    sector: Sector | None = None
    product_scope: str | None = None
    priority: Priority | None = None
    notes: str | None = None
    closed_at: datetime | None = None

    workflow: WorkflowStatus = Field(default_factory=WorkflowStatus)
    team: TeamAssignment = Field(default_factory=TeamAssignment)
    financials: Financials = Field(default_factory=Financials)
    logistics: LogisticsAndDelivery = Field(default_factory=LogisticsAndDelivery)
    design_services: DesignServices | None = None
    corporate_gifting: CorporateGifting | None = None

    class Settings:
        name = "projects"
