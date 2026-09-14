"""
Stage Qualified Student List import schemas.
"""
from __future__ import annotations

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class StageImportPreviewItem(BaseModel):
    row_index: int
    roll_number: str
    student_name: str | None = None
    category: str  # "MATCHED", "ALREADY_AT_STAGE", "NOT_APPLIED", "UNKNOWN_REG_NO", "DUPLICATE_IN_FILE"
    student_user_id: UUID | None = None
    branch_code: str | None = None
    cgpa: float | None = None
    current_status: str | None = None
    details: str | None = None


class StageImportPreviewResponse(BaseModel):
    drive_id: UUID
    stage_id: UUID
    stage_name: str
    stage_sequence: int
    filename: str
    detected_headers: list[str]
    detected_mappings: dict[str, str]
    total_rows: int
    matched_count: int
    already_at_stage_count: int
    not_applied_count: int
    unknown_count: int
    duplicate_count: int
    can_confirm: bool
    items: list[StageImportPreviewItem]
    valid_student_ids: list[UUID] = Field(default_factory=list)


class StageImportConfirmRequest(BaseModel):
    filename: str = "round_qualified.xlsx"
    student_ids: list[UUID]


class StageImportConfirmResponse(BaseModel):
    drive_id: UUID
    stage_id: UUID
    stage_name: str
    total_submitted: int
    newly_assigned_count: int
    already_assigned_count: int
    message: str


class StageQualifiedStudentItem(BaseModel):
    assignment_id: UUID
    stage_id: UUID
    student_user_id: UUID
    roll_number: str
    full_name: str
    email: str
    branch_code: str
    cgpa: float
    status: str
    assigned_at: datetime
