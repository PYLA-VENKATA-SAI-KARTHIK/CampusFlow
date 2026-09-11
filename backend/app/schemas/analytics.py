"""
Analytics Pydantic Schemas.
"""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# -----------------------------------------------------------------------------
# Drive-Level Analytics Schemas
# -----------------------------------------------------------------------------

class DriveAnalyticsSummary(BaseModel):
    eligible_count: int = Field(0, description="Total active students eligible for this drive")
    registered_count: int = Field(0, description="Total valid registrations (status=REGISTERED)")
    registration_rate_percentage: float = Field(0.0, description="Percentage of eligible students who registered")
    total_shortlisted_count: int = Field(0, description="Distinct count of students shortlisted in at least one stage")
    total_selected_count: int = Field(0, description="Distinct count of students selected")
    overall_conversion_percentage: float = Field(0.0, description="Percentage of registered students who were selected")

    model_config = ConfigDict(extra="ignore")


class StageFunnelItem(BaseModel):
    stage_id: UUID
    name: str
    stage_type: str
    sequence_order: int
    is_published: bool
    assigned_count: int = Field(0, description="Total students assigned to this stage")
    shortlisted_count: int = Field(0, description="Students with status SHORTLISTED in this stage")
    appeared_count: int = Field(0, description="Students with status APPEARED in this stage")
    selected_count: int = Field(0, description="Students with status SELECTED in this stage")
    rejected_count: int = Field(0, description="Students with status REJECTED in this stage")

    model_config = ConfigDict(extra="ignore")


class DriveBranchBreakdownItem(BaseModel):
    branch_code: str
    branch_name: str
    eligible_count: int = 0
    registered_count: int = 0
    shortlisted_count: int = 0
    selected_count: int = 0

    model_config = ConfigDict(extra="ignore")


class DriveAnalyticsResponse(BaseModel):
    drive_id: UUID
    title: str
    company_name: str
    job_role: str
    status: str
    summary: DriveAnalyticsSummary
    stage_funnel: list[StageFunnelItem] = Field(default_factory=list)
    branch_breakdown: list[DriveBranchBreakdownItem] = Field(default_factory=list)

    model_config = ConfigDict(extra="ignore")


# -----------------------------------------------------------------------------
# Platform-Wide / Overview Analytics Schemas
# -----------------------------------------------------------------------------

class DrivesSummary(BaseModel):
    total_drives: int = 0
    active_drives: int = 0
    completed_drives: int = 0
    draft_drives: int = 0

    model_config = ConfigDict(extra="ignore")


class PlacementMetrics(BaseModel):
    total_active_students: int = 0
    total_placed_students: int = 0
    overall_placement_percentage: float = 0.0
    total_applications_submitted: int = 0
    average_ctc_lpa: float | None = None
    highest_ctc_lpa: float | None = None

    model_config = ConfigDict(extra="ignore")


class BranchPlacementStat(BaseModel):
    branch_code: str
    branch_name: str
    total_students: int = 0
    placed_students: int = 0
    placement_percentage: float = 0.0

    model_config = ConfigDict(extra="ignore")


class RecentDriveActivity(BaseModel):
    drive_id: UUID
    title: str
    company_name: str
    job_role: str
    status: str
    registered_count: int = 0
    selected_count: int = 0
    created_at: datetime

    model_config = ConfigDict(extra="ignore")


class OverviewAnalyticsResponse(BaseModel):
    drives_summary: DrivesSummary
    placement_metrics: PlacementMetrics
    branch_placement_stats: list[BranchPlacementStat] = Field(default_factory=list)
    recent_drives_activity: list[RecentDriveActivity] = Field(default_factory=list)

    model_config = ConfigDict(extra="ignore")
