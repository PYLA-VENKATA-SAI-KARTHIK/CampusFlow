"""
Common schema types.
"""
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    has_next: bool

    model_config = ConfigDict(from_attributes=True)


class ErrorDetail(BaseModel):
    type: str
    title: str
    status: int
    detail: str
    instance: str | None = None
    reasons: list[str] | None = None
