"""
Stage Assignment schemas.
"""
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

AssignmentStatus = Literal["SHORTLISTED", "APPEARED", "SELECTED", "REJECTED"]


class StageShortlistRequest(BaseModel):
    student_ids: list[UUID] = Field(..., min_length=1)


class StageAssignmentUpdate(BaseModel):
    status: AssignmentStatus | None = None
    result_notes: str | None = None


class StageAssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    stage_id: UUID
    student_user_id: UUID
    drive_id: UUID
    status: AssignmentStatus
    result_notes: str | None
    assigned_at: datetime
    updated_at: datetime

