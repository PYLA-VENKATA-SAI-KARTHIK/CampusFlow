"""
Drive Registration schemas.
"""
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DriveRegistrationResponse(BaseModel):
    id: UUID
    drive_id: UUID
    student_user_id: UUID
    resume_gcs_path_at_registration: str
    status: str
    registered_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RegistrationStudentSummary(BaseModel):
    id: UUID
    user_id: UUID
    full_name: str
    email: str
    roll_number: str
    branch: str
    batch_year: int
    cgpa: float
    active_backlogs: int
    gender: str | None = None
    avatar_url: str | None = None


class DriveRegistrationWithStudentResponse(DriveRegistrationResponse):
    student: RegistrationStudentSummary


class CurrentStageSummary(BaseModel):
    stage_name: str
    stage_status: str
    scheduled_at: datetime | None = None


class StudentApplicationResponse(BaseModel):
    registration_id: UUID
    drive_id: UUID
    drive_title: str
    company_name: str
    company_logo_url: str | None = None
    registered_at: datetime
    drive_status: str
    my_current_stage: CurrentStageSummary | None = None
