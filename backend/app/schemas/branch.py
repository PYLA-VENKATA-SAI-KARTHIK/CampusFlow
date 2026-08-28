"""
Branch schemas.
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BranchBase(BaseModel):
    code: str = Field(..., max_length=20, pattern=r"^[A-Z0-9_]+$")
    name: str = Field(..., max_length=100)


class BranchCreate(BranchBase):
    pass


class BranchUpdate(BaseModel):
    name: str | None = Field(None, max_length=100)
    is_active: bool | None = None


class BranchResponse(BranchBase):
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
