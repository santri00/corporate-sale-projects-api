"""Shared value objects and the camelCase base model."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, EmailStr
from pydantic.alias_generators import to_camel


def document_alias(field_name: str) -> str:
    """camelCase alias generator for Beanie documents.

    ``id`` must map to Mongo's ``_id``; every other field goes camelCase.
    Without the ``id`` special-case a plain ``to_camel`` would clobber Beanie's
    own ``_id`` alias and Mongo would assign an ``ObjectId`` instead.
    """

    return "_id" if field_name == "id" else to_camel(field_name)


def utcnow() -> datetime:
    """Naive UTC timestamp.

    Stored values are naive so comparisons stay consistent between a real
    MongoDB (Motor returns naive by default) and the in-process test mock.
    """

    return datetime.now(UTC).replace(tzinfo=None)


class CamelModel(BaseModel):
    """Base model: snake_case in Python, camelCase on the wire."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class Address(CamelModel):
    line1: str
    line2: str | None = None
    city: str
    state: str
    postal_code: str
    country: str


class Contact(CamelModel):
    name: str
    email: EmailStr | None = None
    phone: str | None = None
