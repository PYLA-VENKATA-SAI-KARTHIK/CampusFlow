"""
PlacementDrive schemas.
"""
from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EligibilityCriteriaBase(BaseModel):
    min_cgpa: float | None = Field(None, ge=0.0, le=10.0)
    max_active_backlogs: int | None = Field(None, ge=0)
    eligible_branches: list[str] | None = None
    eligible_batch_years: list[int] | None = None
    gender: Literal["MALE", "FEMALE", "OTHER"] | None = None

    model_config = ConfigDict(extra="allow")  # Extensible JSONB


class CompanyBrief(BaseModel):
    id: UUID
    name: str
    logo_gcs_path: str | None = None

    model_config = ConfigDict(from_attributes=True)


class PlacementDriveBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    job_role: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    ctc_lpa: float | None = Field(None, ge=0.0)
    stipend_monthly: float | None = Field(None, ge=0.0)
    location: str | None = Field(None, max_length=255)
    bond_details: str | None = None
    registration_deadline: datetime | None = None


class PlacementDriveCreate(PlacementDriveBase):
    company_id: UUID
    eligibility_criteria: EligibilityCriteriaBase


class PlacementDriveUpdate(BaseModel):
    """Used for updating a drive in DRAFT status."""
    title: str | None = Field(None, min_length=1, max_length=255)
    job_role: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    ctc_lpa: float | None = Field(None, ge=0.0)
    stipend_monthly: float | None = Field(None, ge=0.0)
    location: str | None = Field(None, max_length=255)
    bond_details: str | None = None
    registration_deadline: datetime | None = None
    eligibility_criteria: dict[str, Any] | None = None


DriveStatus = Literal[
    "DRAFT",
    "PUBLISHED",
    "REGISTRATION_OPEN",
    "REGISTRATION_CLOSED",
    "SHORTLISTING",
    "ASSESSMENT",
    "INTERVIEW",
    "RESULT",
    "COMPLETED"
]


class PlacementDriveStatusUpdate(BaseModel):
    status: DriveStatus


class EligibilityResult(BaseModel):
    is_eligible: bool
    reasons: list[str]


class PlacementDriveResponse(PlacementDriveBase):
    id: UUID
    company_id: UUID
    status: str
    created_by_user_id: UUID
    published_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    
    company: CompanyBrief | None = None
    eligibility_criteria: dict[str, Any] | None = None
    
    # Optional fields for student requests
    my_eligibility: EligibilityResult | None = None
    is_registered: bool | None = None

    @field_validator("eligibility_criteria", mode="before")
    @classmethod
    def extract_criteria(cls, v: Any) -> Any:
        if hasattr(v, "criteria"):
            return v.criteria
        return v

    model_config = ConfigDict(from_attributes=True)
