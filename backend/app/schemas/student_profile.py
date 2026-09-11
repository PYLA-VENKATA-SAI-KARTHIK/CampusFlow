"""
Student Profile schemas.
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.user import UserResponse
from app.schemas.branch import BranchResponse


class StudentProfileBase(BaseModel):
    roll_number: str = Field(..., max_length=50)
    batch_year: int = Field(..., ge=1900, le=2100)
    cgpa: float = Field(..., ge=0.0, le=10.0)
    active_backlogs: int = Field(..., ge=0)
    phone_number: str | None = Field(None, max_length=15)
    gender: str | None = Field(None, max_length=10)
    resume_gcs_path: str | None = None
    avatar_gcs_path: str | None = None


class StudentProfileCreate(StudentProfileBase):
    branch_code: str = Field(..., max_length=20)


class StudentProfileUpdate(BaseModel):
    phone_number: str | None = Field(None, max_length=15)
    gender: str | None = Field(None, max_length=10)
    avatar_gcs_path: str | None = None

    model_config = ConfigDict(extra="allow")


class StudentProfileResponse(StudentProfileBase):
    id: UUID
    user_id: UUID
    branch_code: str
    resume_uploaded_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    # Included relationships
    user: UserResponse | None = None
    branch: BranchResponse | None = None

    model_config = ConfigDict(from_attributes=True)

class ResumeUploadUrlResponse(BaseModel):
    upload_url: str
    object_path: str
    expires_in: int

class ResumeConfirmRequest(BaseModel):
    object_path: str
