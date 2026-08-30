from __future__ import annotations

from datetime import datetime
from uuid import UUID

from app.models.common import Address, CamelModel, Contact
from app.models.enums import ClientType, PaymentTerms


class ClientCreate(CamelModel):
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


class ClientUpdate(CamelModel):
    company_name: str | None = None
    client_type: ClientType | None = None
    industry: str | None = None
    region: str | None = None
    address: Address | None = None
    point_of_contact: Contact | None = None
    payment_terms: PaymentTerms | None = None
    website_url: str | None = None
    is_first_time_client: bool | None = None
    procurement_method: str | None = None
    remarks: str | None = None


class ClientRead(CamelModel):
    id: UUID
    created_at: datetime
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
