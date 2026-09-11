"""
Analytics Repository.
Executes high-performance SQL aggregate queries for Drive-level and Platform-wide analytics.
"""
from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.branch import Branch
from app.models.company import Company
from app.models.drive_registration import DriveRegistration
from app.models.placement_drive import PlacementDrive
from app.models.placement_stage import PlacementStage
from app.models.stage_assignment import StageAssignment
from app.models.student_profile import StudentProfile
from app.models.user import User


class AnalyticsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # -------------------------------------------------------------------------
    # Drive-Level Analytics Queries
    # -------------------------------------------------------------------------

    async def get_drive_registered_count(self, drive_id: UUID) -> int:
        """Count valid registrations (status='REGISTERED') for a drive."""
        stmt = (
            select(func.count(DriveRegistration.id))
            .where(
                DriveRegistration.drive_id == drive_id,
                DriveRegistration.status == "REGISTERED",
            )
        )
        return await self.session.scalar(stmt) or 0

    async def get_drive_distinct_shortlisted_and_selected(
        self, drive_id: UUID
    ) -> tuple[int, int]:
        """
        Return (distinct_shortlisted_count, distinct_selected_count) for a drive.
        Uses stage_assignments.drive_id denormalization.
        """
        shortlisted_stmt = (
            select(func.count(func.distinct(StageAssignment.student_user_id)))
            .where(
                StageAssignment.drive_id == drive_id,
                StageAssignment.status.in_(("SHORTLISTED", "SELECTED")),
            )
        )
        selected_stmt = (
            select(func.count(func.distinct(StageAssignment.student_user_id)))
            .where(
                StageAssignment.drive_id == drive_id,
                StageAssignment.status == "SELECTED",
            )
        )
        shortlisted_count = await self.session.scalar(shortlisted_stmt) or 0
        selected_count = await self.session.scalar(selected_stmt) or 0
        return shortlisted_count, selected_count

    async def get_drive_stage_funnel(self, drive_id: UUID) -> list[dict[str, Any]]:
        """
        Query stage-by-stage counts (assigned, shortlisted, appeared, selected, rejected)
        ordered by sequence_order ASC.
        """
        stmt = (
            select(
                PlacementStage.id.label("stage_id"),
                PlacementStage.name.label("name"),
                PlacementStage.stage_type.label("stage_type"),
                PlacementStage.sequence_order.label("sequence_order"),
                PlacementStage.is_published.label("is_published"),
                func.count(StageAssignment.id).label("assigned_count"),
                func.count(
                    case((StageAssignment.status == "SHORTLISTED", 1))
                ).label("shortlisted_count"),
                func.count(
                    case((StageAssignment.status == "APPEARED", 1))
                ).label("appeared_count"),
                func.count(
                    case((StageAssignment.status == "SELECTED", 1))
                ).label("selected_count"),
                func.count(
                    case((StageAssignment.status == "REJECTED", 1))
                ).label("rejected_count"),
            )
            .select_from(PlacementStage)
            .outerjoin(
                StageAssignment, StageAssignment.stage_id == PlacementStage.id
            )
            .where(PlacementStage.drive_id == drive_id)
            .group_by(
                PlacementStage.id,
                PlacementStage.name,
                PlacementStage.stage_type,
                PlacementStage.sequence_order,
                PlacementStage.is_published,
            )
            .order_by(PlacementStage.sequence_order.asc())
        )
        result = await self.session.execute(stmt)
        rows = result.mappings().all()
        return [dict(r) for r in rows]

    async def get_drive_branch_counts(
        self, drive_id: UUID
    ) -> list[dict[str, Any]]:
        """
        Aggregate registered, shortlisted, and selected counts per active branch for a drive.
        """
        # 1. Fetch active branches
        branches_stmt = (
            select(Branch)
            .where(Branch.is_active == True)  # noqa: E712
            .order_by(Branch.code.asc())
        )
        branches_res = await self.session.execute(branches_stmt)
        branches = branches_res.scalars().all()

        # 2. Registered counts per branch
        reg_stmt = (
            select(
                StudentProfile.branch_code,
                func.count(func.distinct(DriveRegistration.student_user_id)).label("reg_count"),
            )
            .select_from(DriveRegistration)
            .join(StudentProfile, StudentProfile.user_id == DriveRegistration.student_user_id)
            .where(
                DriveRegistration.drive_id == drive_id,
                DriveRegistration.status == "REGISTERED",
            )
            .group_by(StudentProfile.branch_code)
        )
        reg_res = await self.session.execute(reg_stmt)
        reg_map = {row.branch_code: row.reg_count for row in reg_res.all()}

        # 3. Shortlisted & Selected counts per branch
        stage_stmt = (
            select(
                StudentProfile.branch_code,
                func.count(
                    func.distinct(
                        case(
                            (StageAssignment.status.in_(("SHORTLISTED", "SELECTED")), StageAssignment.student_user_id)
                        )
                    )
                ).label("shortlisted_count"),
                func.count(
                    func.distinct(
                        case((StageAssignment.status == "SELECTED", StageAssignment.student_user_id))
                    )
                ).label("selected_count"),
            )
            .select_from(StageAssignment)
            .join(StudentProfile, StudentProfile.user_id == StageAssignment.student_user_id)
            .where(StageAssignment.drive_id == drive_id)
            .group_by(StudentProfile.branch_code)
        )
        stage_res = await self.session.execute(stage_stmt)
        stage_map = {
            row.branch_code: {
                "shortlisted": row.shortlisted_count,
                "selected": row.selected_count,
            }
            for row in stage_res.all()
        }

        # Combine into complete list
        result = []
        for b in branches:
            branch_stage = stage_map.get(b.code, {"shortlisted": 0, "selected": 0})
            result.append({
                "branch_code": b.code,
                "branch_name": b.name,
                "registered_count": reg_map.get(b.code, 0),
                "shortlisted_count": branch_stage["shortlisted"],
                "selected_count": branch_stage["selected"],
            })
        return result

    # -------------------------------------------------------------------------
    # Platform-Wide / Overview Analytics Queries
    # -------------------------------------------------------------------------

    async def get_overview_drives_summary(self) -> dict[str, Any]:
        """Aggregate total drives by status and CTC statistics."""
        stmt = select(
            func.count(PlacementDrive.id).label("total_drives"),
            func.count(
                case((PlacementDrive.status == "DRAFT", 1))
            ).label("draft_drives"),
            func.count(
                case((PlacementDrive.status == "COMPLETED", 1))
            ).label("completed_drives"),
            func.count(
                case((PlacementDrive.status.notin_(("DRAFT", "COMPLETED")), 1))
            ).label("active_drives"),
            func.avg(PlacementDrive.ctc_lpa).label("avg_ctc"),
            func.max(PlacementDrive.ctc_lpa).label("max_ctc"),
        )
        result = await self.session.execute(stmt)
        row = result.mappings().first()
        if not row:
            return {
                "total_drives": 0,
                "draft_drives": 0,
                "completed_drives": 0,
                "active_drives": 0,
                "avg_ctc": None,
                "max_ctc": None,
            }
        return dict(row)

    async def get_overview_student_and_placement_counts(self) -> dict[str, Any]:
        """
        Aggregate total active students, total distinct placed students,
        and total applications submitted.
        """
        # 1. Total active students
        total_students_stmt = select(func.count(User.id)).where(
            User.role == "STUDENT",
            User.is_active == True,  # noqa: E712
        )
        total_active_students = await self.session.scalar(total_students_stmt) or 0

        # 2. Total distinct placed students
        placed_students_stmt = select(
            func.count(func.distinct(StageAssignment.student_user_id))
        ).where(StageAssignment.status == "SELECTED")
        total_placed_students = await self.session.scalar(placed_students_stmt) or 0

        # 3. Total applications submitted
        total_apps_stmt = select(func.count(DriveRegistration.id)).where(
            DriveRegistration.status == "REGISTERED"
        )
        total_applications = await self.session.scalar(total_apps_stmt) or 0

        return {
            "total_active_students": total_active_students,
            "total_placed_students": total_placed_students,
            "total_applications_submitted": total_applications,
        }

    async def get_overview_branch_placement_stats(self) -> list[dict[str, Any]]:
        """
        Calculate total active students and placed students grouped by branch.
        """
        # Active branches
        branches_stmt = (
            select(Branch)
            .where(Branch.is_active == True)  # noqa: E712
            .order_by(Branch.code.asc())
        )
        branches = (await self.session.execute(branches_stmt)).scalars().all()

        # Total active students per branch
        students_stmt = (
            select(
                StudentProfile.branch_code,
                func.count(StudentProfile.id).label("total_students"),
            )
            .select_from(StudentProfile)
            .join(User, StudentProfile.user_id == User.id)
            .where(User.is_active == True, User.role == "STUDENT")  # noqa: E712
            .group_by(StudentProfile.branch_code)
        )
        students_res = await self.session.execute(students_stmt)
        total_students_map = {row.branch_code: row.total_students for row in students_res.all()}

        # Placed students per branch
        placed_stmt = (
            select(
                StudentProfile.branch_code,
                func.count(func.distinct(StageAssignment.student_user_id)).label("placed_count"),
            )
            .select_from(StageAssignment)
            .join(StudentProfile, StudentProfile.user_id == StageAssignment.student_user_id)
            .where(StageAssignment.status == "SELECTED")
            .group_by(StudentProfile.branch_code)
        )
        placed_res = await self.session.execute(placed_stmt)
        placed_map = {row.branch_code: row.placed_count for row in placed_res.all()}

        result = []
        for b in branches:
            total_b = total_students_map.get(b.code, 0)
            placed_b = placed_map.get(b.code, 0)
            pct = round((placed_b / total_b) * 100, 2) if total_b > 0 else 0.0
            result.append({
                "branch_code": b.code,
                "branch_name": b.name,
                "total_students": total_b,
                "placed_students": placed_b,
                "placement_percentage": pct,
            })
        return result

    async def get_recent_drives_activity(self, limit: int = 5) -> list[dict[str, Any]]:
        """Fetch recent drives with company name, registered and selected candidate counts."""
        stmt = (
            select(
                PlacementDrive.id.label("drive_id"),
                PlacementDrive.title.label("title"),
                Company.name.label("company_name"),
                PlacementDrive.job_role.label("job_role"),
                PlacementDrive.status.label("status"),
                PlacementDrive.created_at.label("created_at"),
                func.count(
                    func.distinct(
                        case((DriveRegistration.status == "REGISTERED", DriveRegistration.student_user_id))
                    )
                ).label("registered_count"),
                func.count(
                    func.distinct(
                        case((StageAssignment.status == "SELECTED", StageAssignment.student_user_id))
                    )
                ).label("selected_count"),
            )
            .select_from(PlacementDrive)
            .join(Company, PlacementDrive.company_id == Company.id)
            .outerjoin(DriveRegistration, DriveRegistration.drive_id == PlacementDrive.id)
            .outerjoin(StageAssignment, StageAssignment.drive_id == PlacementDrive.id)
            .group_by(PlacementDrive.id, Company.name)
            .order_by(PlacementDrive.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        rows = result.mappings().all()
        return [dict(r) for r in rows]
