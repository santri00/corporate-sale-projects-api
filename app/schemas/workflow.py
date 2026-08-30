from __future__ import annotations

from datetime import date

from app.models.common import CamelModel
from app.models.enums import WorkflowState


class TriggersPatch(CamelModel):
    is_quote_requested: bool | None = None
    is_product_finalized: bool | None = None
    is_split_requested: bool | None = None
    requires_design_services: bool | None = None


class WorkflowPatch(CamelModel):
    status: WorkflowState | None = None
    delivery_need_by_date: date | None = None
    triggers: TriggersPatch | None = None
