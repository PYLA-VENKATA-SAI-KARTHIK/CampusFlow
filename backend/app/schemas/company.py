"""
Company schemas.
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class CompanyBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    website: str | None = None
    logo_gcs_path: str | None = None
    industry: str | None = Field(None, max_length=100)
    description: str | None = None


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    website: str | None = None
    logo_gcs_path: str | None = None
    industry: str | None = Field(None, max_length=100)
    description: str | None = None


class CompanyResponse(CompanyBase):
    id: UUID
    created_by_user_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
