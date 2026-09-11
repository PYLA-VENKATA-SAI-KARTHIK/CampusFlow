"""
Analytics Service.
Coordinates analytics queries, evaluates eligibility distributions,
computes conversion rates and KPI percentages with zero-denominator safety.
"""
from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import HTTPException, status

from app.models.placement_drive import PlacementDrive
from app.repositories.analytics_repository import AnalyticsRepository
from app.repositories.placement_drive_repository import PlacementDriveRepository
from app.repositories.student_profile_repository import StudentProfileRepository
from app.schemas.analytics import (
    BranchPlacementStat,
    DriveAnalyticsResponse,
    DriveAnalyticsSummary,
    DriveBranchBreakdownItem,
    DrivesSummary,
    OverviewAnalyticsResponse,
    PlacementMetrics,
    RecentDriveActivity,
    StageFunnelItem,
)
from app.services.eligibility_service import EligibilityService


class AnalyticsService:
    def __init__(
        self,
        analytics_repo: AnalyticsRepository,
        drive_repo: PlacementDriveRepository,
        student_repo: StudentProfileRepository,
    ) -> None:
        self.analytics_repo = analytics_repo
        self.drive_repo = drive_repo
        self.student_repo = student_repo

    async def get_drive_analytics(self, drive_id: UUID) -> DriveAnalyticsResponse:
        """
        Compute aggregate analytics for a single placement drive.
        - Validates drive existence (404 if missing)
        - Computes eligible candidate count and branch distribution via EligibilityService
        - Computes stage funnel progression
        - Computes branch-wise breakdown
        """
        drive: PlacementDrive | None = await self.drive_repo.get_by_id(drive_id)
        if not drive:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Placement drive not found.",
            )

        # 1. Calculate eligibility counts across active students
        active_profiles = await self.student_repo.list_all_active_profiles()
        criteria_dict: dict[str, Any] = (
            drive.eligibility_criteria.criteria
            if drive.eligibility_criteria and drive.eligibility_criteria.criteria
            else {}
        )

        eligible_count = 0
        branch_eligible_map: dict[str, int] = {}

        for profile in active_profiles:
            is_eligible, _ = EligibilityService.evaluate(profile, criteria_dict)
            if is_eligible:
                eligible_count += 1
                branch_code = profile.branch_code
                branch_eligible_map[branch_code] = branch_eligible_map.get(branch_code, 0) + 1

        # 2. Registration count
        registered_count = await self.analytics_repo.get_drive_registered_count(drive_id)

        # 3. Shortlisted & Selected distinct counts
        total_shortlisted, total_selected = (
            await self.analytics_repo.get_drive_distinct_shortlisted_and_selected(drive_id)
        )

        # 4. Percentages with zero-denominator safeguards
        registration_rate = (
            round((registered_count / eligible_count) * 100, 2)
            if eligible_count > 0
            else 0.0
        )
        overall_conversion = (
            round((total_selected / registered_count) * 100, 2)
            if registered_count > 0
            else 0.0
        )

        summary = DriveAnalyticsSummary(
            eligible_count=eligible_count,
            registered_count=registered_count,
            registration_rate_percentage=registration_rate,
            total_shortlisted_count=total_shortlisted,
            total_selected_count=total_selected,
            overall_conversion_percentage=overall_conversion,
        )

        # 5. Stage Funnel
        raw_funnel = await self.analytics_repo.get_drive_stage_funnel(drive_id)
        stage_funnel = [
            StageFunnelItem(
                stage_id=item["stage_id"],
                name=item["name"],
                stage_type=item["stage_type"],
                sequence_order=item["sequence_order"],
                is_published=item["is_published"],
                assigned_count=item["assigned_count"],
                shortlisted_count=item["shortlisted_count"],
                appeared_count=item["appeared_count"],
                selected_count=item["selected_count"],
                rejected_count=item["rejected_count"],
            )
            for item in raw_funnel
        ]

        # 6. Branch Breakdown
        raw_branches = await self.analytics_repo.get_drive_branch_counts(drive_id)
        branch_breakdown = [
            DriveBranchBreakdownItem(
                branch_code=b["branch_code"],
                branch_name=b["branch_name"],
                eligible_count=branch_eligible_map.get(b["branch_code"], 0),
                registered_count=b["registered_count"],
                shortlisted_count=b["shortlisted_count"],
                selected_count=b["selected_count"],
            )
            for b in raw_branches
        ]

        company_name = drive.company.name if drive.company else "Unknown Company"

        return DriveAnalyticsResponse(
            drive_id=drive.id,
            title=drive.title,
            company_name=company_name,
            job_role=drive.job_role,
            status=drive.status,
            summary=summary,
            stage_funnel=stage_funnel,
            branch_breakdown=branch_breakdown,
        )

    async def get_overview_analytics(self) -> OverviewAnalyticsResponse:
        """
        Compute platform-wide aggregate placement analytics for Officers and Admins.
        """
        # 1. Drives summary
        drives_summary_raw = await self.analytics_repo.get_overview_drives_summary()
        drives_summary = DrivesSummary(
            total_drives=drives_summary_raw.get("total_drives", 0),
            active_drives=drives_summary_raw.get("active_drives", 0),
            completed_drives=drives_summary_raw.get("completed_drives", 0),
            draft_drives=drives_summary_raw.get("draft_drives", 0),
        )

        # 2. Placement metrics
        counts_raw = await self.analytics_repo.get_overview_student_and_placement_counts()
        total_students = counts_raw.get("total_active_students", 0)
        placed_students = counts_raw.get("total_placed_students", 0)

        placement_rate = (
            round((placed_students / total_students) * 100, 2)
            if total_students > 0
            else 0.0
        )

        avg_ctc = drives_summary_raw.get("avg_ctc")
        max_ctc = drives_summary_raw.get("max_ctc")

        placement_metrics = PlacementMetrics(
            total_active_students=total_students,
            total_placed_students=placed_students,
            overall_placement_percentage=placement_rate,
            total_applications_submitted=counts_raw.get("total_applications_submitted", 0),
            average_ctc_lpa=round(float(avg_ctc), 2) if avg_ctc is not None else None,
            highest_ctc_lpa=round(float(max_ctc), 2) if max_ctc is not None else None,
        )

        # 3. Branch placement stats
        raw_branch_stats = await self.analytics_repo.get_overview_branch_placement_stats()
        branch_stats = [
            BranchPlacementStat(
                branch_code=b["branch_code"],
                branch_name=b["branch_name"],
                total_students=b["total_students"],
                placed_students=b["placed_students"],
                placement_percentage=b["placement_percentage"],
            )
            for b in raw_branch_stats
        ]

        # 4. Recent drives activity
        raw_recent = await self.analytics_repo.get_recent_drives_activity(limit=5)
        recent_activity = [
            RecentDriveActivity(
                drive_id=d["drive_id"],
                title=d["title"],
                company_name=d["company_name"],
                job_role=d["job_role"],
                status=d["status"],
                registered_count=d["registered_count"],
                selected_count=d["selected_count"],
                created_at=d["created_at"],
            )
            for d in raw_recent
        ]

        return OverviewAnalyticsResponse(
            drives_summary=drives_summary,
            placement_metrics=placement_metrics,
            branch_placement_stats=branch_stats,
            recent_drives_activity=recent_activity,
        )
