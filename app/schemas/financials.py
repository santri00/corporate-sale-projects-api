from __future__ import annotations

from datetime import date
from enum import StrEnum

from app.models.common import Address, CamelModel


class ArrayMode(StrEnum):
    replace = "replace"
    append = "append"
    remove = "remove"


class FinancialsPatch(CamelModel):
    budget: float | None = None
    total_sale: float | None = None
    quote_ids: list[str] | None = None
    order_numbers: list[str] | None = None
    billing_address: Address | None = None
    payment_terms: str | None = None
    payment_collected_date: date | None = None
    project_close_date: date | None = None
