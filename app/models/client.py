from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from beanie import Document
from pydantic import ConfigDict, Field

from app.models.common import Address, Contact, document_alias, utcnow
from app.models.enums import ClientType, PaymentTerms


class Client(Document):
    model_config = ConfigDict(alias_generator=document_alias, populate_by_name=True)

    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=utcnow)

    company_name: str
    client_type: ClientType
    industry: str | None = None
    region: str | None = None
    address: Address | None = None
    point_of_contact: Contact | None = None
    payment_terms: PaymentTerms | None = None
    website_url: str | None = None
    is_first_time_client: bool = False
    procurement_method: str | None = None
    remarks: str | None = None

    class Settings:
        name = "clients"
