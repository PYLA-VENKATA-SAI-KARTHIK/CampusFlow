"""
Student Profile schemas.
"""
from datetime import datetime
from uuid import UUID

from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.schemas.user import UserResponse
from app.schemas.branch import BranchResponse


class StudentProfileBase(BaseModel):
    roll_number: str = Field(..., max_length=50)
    batch_year: int = Field(..., ge=1900, le=2100)
    cgpa: float = Field(..., ge=0.0, le=10.0)
    active_backlogs: int = Field(..., ge=0)
    phone_number: str | None = Field(None, max_length=15)
    personal_email: EmailStr | None = None
    gender: str | None = Field(None, max_length=10)
    section: str | None = Field(None, max_length=10)
    tenth_mark: float | None = Field(None, ge=0.0, le=100.0)
    twelfth_mark: float | None = Field(None, ge=0.0, le=100.0)
    diploma_mark: float | None = Field(None, ge=0.0, le=100.0)
    portfolio_url: str | None = Field(None, max_length=500)
    resume_gcs_path: str | None = None
    avatar_gcs_path: str | None = None

    @field_validator("personal_email", mode="before")
    @classmethod
    def normalize_personal_email(cls, v: str | None) -> str | None:
        if v is None:
            return None
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return None
        return v

    @field_validator("portfolio_url")
    @classmethod
    def validate_portfolio_url(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        if not v:
            return None
        parsed = urlparse(v)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise ValueError("Portfolio URL must be a valid HTTP or HTTPS URL.")
        return v


class StudentProfileCreate(StudentProfileBase):
    branch_code: str = Field(..., max_length=20)


class StudentProfileUpdate(BaseModel):
    full_name: str | None = Field(None, min_length=1, max_length=255)
    phone_number: str | None = Field(None, max_length=15)
    personal_email: EmailStr | None = None
    gender: str | None = Field(None, max_length=10)
    section: str | None = Field(None, max_length=10)
    tenth_mark: float | None = Field(None, ge=0.0, le=100.0)
    twelfth_mark: float | None = Field(None, ge=0.0, le=100.0)
    diploma_mark: float | None = Field(None, ge=0.0, le=100.0)
    portfolio_url: str | None = Field(None, max_length=500)
    avatar_gcs_path: str | None = None

    @field_validator("personal_email", mode="before")
    @classmethod
    def normalize_personal_email(cls, v: str | None) -> str | None:
        if v is None:
            return None
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return None
        return v

    @field_validator("portfolio_url")
    @classmethod
    def validate_portfolio_url(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        if not v:
            return None
        parsed = urlparse(v)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise ValueError("Portfolio URL must be a valid HTTP or HTTPS URL.")
        return v

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
