from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import Query

from app.errors import ValidationAppError
from app.models.enums import Priority, ProjectType, WorkflowState
from app.schemas.project import DateField

# user-facing sort token -> stored (camelCase) field path
_SORT_MAP = {
    "createdAt": "createdAt",
    "projectName": "projectName",
    "priority": "priority",
    "status": "workflow.status",
}


def _parse_sort(sort: str) -> tuple[str, int]:
    descending = sort.startswith("-")
    key = sort[1:] if (descending or sort.startswith("+")) else sort
    if key not in _SORT_MAP:
        raise ValidationAppError(
            f"Cannot sort by '{key}'. Allowed fields: {', '.join(sorted(_SORT_MAP))}"
        )
    return _SORT_MAP[key], (-1 if descending else 1)


class PaginationParams:
    def __init__(
        self,
        page: int = Query(1, ge=1),
        size: int = Query(20, ge=1, le=100),
    ) -> None:
        self.page = page
        self.size = size
        self.skip = (page - 1) * size
        self.limit = size


class ProjectFilterParams:
    def __init__(
        self,
        client_name: str | None = Query(None, alias="clientName"),
        client_id: UUID | None = Query(None, alias="clientId"),
        date_from: date | None = Query(None, alias="dateFrom"),
        date_to: date | None = Query(None, alias="dateTo"),
        date_field: DateField = Query(DateField.created_at, alias="dateField"),
        status: WorkflowState | None = Query(None),
        project_type: ProjectType | None = Query(None, alias="projectType"),
        priority: Priority | None = Query(None),
        sort: str = Query("-createdAt"),
    ) -> None:
        if date_from and date_to and date_from > date_to:
            raise ValidationAppError("dateFrom must be on or before dateTo")

        self.client_name = client_name
        self.client_id = client_id
        self.date_from = date_from
        self.date_to = date_to
        self.date_field = date_field
        self.status = status
        self.project_type = project_type
        self.priority = priority
        self.sort_field, self.sort_dir = _parse_sort(sort)
