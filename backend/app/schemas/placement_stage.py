"""
Placement Stage schemas.
"""
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

StageType = Literal["APTITUDE", "TECHNICAL", "HR", "GD", "CODING", "OTHER"]

class PlacementStageBase(BaseModel):
    name: str = Field(..., max_length=255)
    stage_type: StageType
    sequence_order: int = Field(..., ge=1)
    scheduled_at: datetime | None = None
    location_or_link: str | None = None
    instructions: str | None = None


class PlacementStageCreate(PlacementStageBase):
    pass


class PlacementStageUpdate(BaseModel):
    name: str | None = Field(None, max_length=255)
    stage_type: StageType | None = None
    sequence_order: int | None = Field(None, ge=1)
    scheduled_at: datetime | None = None
    location_or_link: str | None = None
    instructions: str | None = None


class PlacementStageResponse(PlacementStageBase):
    id: UUID
    drive_id: UUID
    is_published: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
