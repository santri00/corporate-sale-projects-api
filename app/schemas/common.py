from __future__ import annotations

from typing import Generic, TypeVar

from app.models.common import CamelModel

T = TypeVar("T")


class Pagination(CamelModel):
    page: int
    size: int
    total: int
    pages: int


class Page(CamelModel, Generic[T]):
    items: list[T]
    pagination: Pagination
