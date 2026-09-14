"""
Placement Drive Stage Qualified List Import Service.
"""
from __future__ import annotations

import logging
from typing import Sequence
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.audit_log import AuditLog
from app.models.drive_registration import DriveRegistration
from app.models.placement_drive import PlacementDrive
from app.models.placement_stage import PlacementStage
from app.models.stage_assignment import StageAssignment
from app.models.student_profile import StudentProfile
from app.models.user import User
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.drive_registration_repository import DriveRegistrationRepository
from app.repositories.placement_drive_repository import PlacementDriveRepository
from app.repositories.placement_stage_repository import PlacementStageRepository
from app.repositories.stage_assignment_repository import StageAssignmentRepository
from app.schemas.stage_import import (
    StageImportConfirmRequest,
    StageImportConfirmResponse,
    StageImportPreviewItem,
    StageImportPreviewResponse,
    StageQualifiedStudentItem,
)
from app.services.notification_dispatcher import NotificationDispatcher
from app.utils.excel_importer import (
    detect_column_mappings,
    normalize_cell_as_string,
    parse_tabular_file,
)

logger = logging.getLogger(__name__)


class StageImportService:
    def __init__(
        self,
        session: AsyncSession,
        dispatcher: NotificationDispatcher | None = None,
    ) -> None:
        self.session = session
        self.dispatcher = dispatcher
        self.stage_repo = PlacementStageRepository(session)
        self.drive_repo = PlacementDriveRepository(session)
        self.assignment_repo = StageAssignmentRepository(session)
        self.registration_repo = DriveRegistrationRepository(session)
        self.audit_repo = AuditLogRepository(session)

    async def preview_stage_qualified_import(
        self,
        drive_id: UUID,
        stage_id: UUID,
        file_bytes: bytes,
        filename: str,
        custom_mapping: dict[str, str] | None = None,
    ) -> StageImportPreviewResponse:
        """
        Parses company-provided qualified student list for a specific stage.
        Matches Registration Numbers strictly against applicants registered for this drive.
        Categorizes rows into: MATCHED, ALREADY_AT_STAGE, NOT_APPLIED, UNKNOWN_REG_NO, DUPLICATE_IN_FILE.
        Does not mutate the database.
        """
        # 1. Validate Drive & Stage
        drive = await self.drive_repo.get_by_id(drive_id)
        if not drive:
            raise HTTPException(status_code=404, detail="Placement drive not found.")

        stage = await self.stage_repo.get_by_id(stage_id)
        if not stage or stage.drive_id != drive_id:
            raise HTTPException(status_code=404, detail="Placement stage not found for this drive.")

        # 2. Parse file
        headers, raw_rows = parse_tabular_file(file_bytes, filename)
        detected_mappings = detect_column_mappings(headers)
        if custom_mapping:
            detected_mappings.update(custom_mapping)

        reg_col = detected_mappings.get("roll_number")
        name_col = detected_mappings.get("full_name")

        if not reg_col:
            return StageImportPreviewResponse(
                drive_id=drive_id,
                stage_id=stage_id,
                stage_name=stage.name,
                stage_sequence=stage.sequence_order,
                filename=filename,
                detected_headers=headers,
                detected_mappings=detected_mappings,
                total_rows=len(raw_rows),
                matched_count=0,
                already_at_stage_count=0,
                not_applied_count=0,
                unknown_count=len(raw_rows),
                duplicate_count=0,
                can_confirm=False,
                items=[],
                valid_student_ids=[],
            )

        # 3. Pre-fetch drive applicants (DriveRegistration + StudentProfile + User)
        stmt_reg = (
            select(DriveRegistration, StudentProfile, User)
            .join(StudentProfile, DriveRegistration.student_user_id == StudentProfile.user_id)
            .join(User, DriveRegistration.student_user_id == User.id)
            .where(DriveRegistration.drive_id == drive_id)
        )
        reg_rows = (await self.session.execute(stmt_reg)).all()
        registered_by_roll: dict[str, tuple[DriveRegistration, StudentProfile, User]] = {}
        for reg, profile, user in reg_rows:
            if profile.roll_number:
                registered_by_roll[profile.roll_number.strip().lower()] = (reg, profile, user)

        # 4. Pre-fetch all master profiles to detect if student is in college master list vs completely unknown
        stmt_master = select(StudentProfile.roll_number, StudentProfile.user_id)
        master_rows = (await self.session.execute(stmt_master)).all()
        master_by_roll: dict[str, UUID] = {
            r[0].strip().lower(): r[1] for r in master_rows if r[0]
        }

        # 5. Pre-fetch existing assignments for this stage
        existing_assignments = await self.assignment_repo.list_assignments_for_stage(stage_id)
        existing_assigned_user_ids = {a.student_user_id: a for a in existing_assignments}

        # 6. Process rows and categorize
        seen_in_file: set[str] = set()
        items: list[StageImportPreviewItem] = []
        valid_student_ids: list[UUID] = []

        matched_count = 0
        already_at_stage_count = 0
        not_applied_count = 0
        unknown_count = 0
        dup_count = 0

        for idx, row in enumerate(raw_rows, start=1):
            raw_reg = row.get(reg_col, "")
            clean_reg = normalize_cell_as_string(raw_reg).strip()
            raw_name = normalize_cell_as_string(row.get(name_col, "")).strip() if name_col else None

            if not clean_reg:
                unknown_count += 1
                items.append(
                    StageImportPreviewItem(
                        row_index=idx,
                        roll_number="—",
                        student_name=raw_name,
                        category="UNKNOWN_REG_NO",
                        details="Registration number is empty",
                    )
                )
                continue

            reg_lower = clean_reg.lower()

            if reg_lower in seen_in_file:
                dup_count += 1
                items.append(
                    StageImportPreviewItem(
                        row_index=idx,
                        roll_number=clean_reg,
                        student_name=raw_name,
                        category="DUPLICATE_IN_FILE",
                        details=f"Duplicate registration number in file: {clean_reg}",
                    )
                )
                continue

            seen_in_file.add(reg_lower)

            # Check matching against applicants
            if reg_lower in registered_by_roll:
                reg, profile, user = registered_by_roll[reg_lower]
                display_name = user.full_name or raw_name or f"Student {clean_reg}"

                if user.id in existing_assigned_user_ids:
                    current_assign = existing_assigned_user_ids[user.id]
                    already_at_stage_count += 1
                    valid_student_ids.append(user.id)
                    items.append(
                        StageImportPreviewItem(
                            row_index=idx,
                            roll_number=clean_reg,
                            student_name=display_name,
                            category="ALREADY_AT_STAGE",
                            student_user_id=user.id,
                            branch_code=profile.branch_code,
                            cgpa=profile.cgpa,
                            current_status=current_assign.status,
                            details=f"Already qualified/assigned to {stage.name} ({current_assign.status})",
                        )
                    )
                else:
                    matched_count += 1
                    valid_student_ids.append(user.id)
                    items.append(
                        StageImportPreviewItem(
                            row_index=idx,
                            roll_number=clean_reg,
                            student_name=display_name,
                            category="MATCHED",
                            student_user_id=user.id,
                            branch_code=profile.branch_code,
                            cgpa=profile.cgpa,
                            current_status=reg.status,
                            details=f"Registered applicant matched — ready to qualify for {stage.name}",
                        )
                    )
            elif reg_lower in master_by_roll:
                # Student exists in Master List, but never applied for this drive
                not_applied_count += 1
                items.append(
                    StageImportPreviewItem(
                        row_index=idx,
                        roll_number=clean_reg,
                        student_name=raw_name,
                        category="NOT_APPLIED",
                        details="Student exists in college master list but has NOT applied to this drive",
                    )
                )
            else:
                # Registration number not found anywhere in Master List
                unknown_count += 1
                items.append(
                    StageImportPreviewItem(
                        row_index=idx,
                        roll_number=clean_reg,
                        student_name=raw_name,
                        category="UNKNOWN_REG_NO",
                        details="Registration number does not exist in Master Student List",
                    )
                )

        unique_valid_ids = list(dict.fromkeys(valid_student_ids))

        return StageImportPreviewResponse(
            drive_id=drive_id,
            stage_id=stage_id,
            stage_name=stage.name,
            stage_sequence=stage.sequence_order,
            filename=filename,
            detected_headers=headers,
            detected_mappings=detected_mappings,
            total_rows=len(raw_rows),
            matched_count=matched_count,
            already_at_stage_count=already_at_stage_count,
            not_applied_count=not_applied_count,
            unknown_count=unknown_count,
            duplicate_count=dup_count,
            can_confirm=len(unique_valid_ids) > 0,
            items=items,
            valid_student_ids=unique_valid_ids,
        )

    async def confirm_stage_qualified_import(
        self,
        drive_id: UUID,
        stage_id: UUID,
        request: StageImportConfirmRequest,
        current_user_id: UUID,
    ) -> StageImportConfirmResponse:
        """
        Commits qualified students to the drive stage.
        - Idempotently creates or updates StageAssignment with status='SHORTLISTED'.
        - Updates DriveRegistration status to 'SHORTLISTED' if currently 'REGISTERED'.
        - Does NOT auto-reject non-shortlisted applicants.
        - Automatically marks stage as published so qualified students see their progression.
        - Logs immutable STAGE_QUALIFIED_IMPORT_CONFIRMED in AuditLog.
        """
        # 1. Validate Drive and Stage
        drive = await self.drive_repo.get_by_id(drive_id)
        if not drive:
            raise HTTPException(status_code=404, detail="Placement drive not found.")

        stage = await self.stage_repo.get_by_id(stage_id)
        if not stage or stage.drive_id != drive_id:
            raise HTTPException(status_code=404, detail="Placement stage not found for this drive.")

        # 2. Deduplicate and verify all student IDs are registered for this drive
        unique_student_ids = list(dict.fromkeys(request.student_ids))
        if not unique_student_ids:
            raise HTTPException(status_code=422, detail="No student IDs provided for confirmation.")

        registered_ids = await self.registration_repo.get_registered_student_ids_for_drive_and_students(
            drive_id, unique_student_ids
        )

        valid_student_ids = [sid for sid in unique_student_ids if sid in registered_ids]
        if not valid_student_ids:
            raise HTTPException(
                status_code=422,
                detail="None of the specified students are registered applicants for this drive.",
            )

        # 3. Check existing stage assignments
        existing_assignments = await self.assignment_repo.list_assignments_for_stage_and_students(
            stage_id, valid_student_ids
        )
        already_assigned_ids = {a.student_user_id for a in existing_assignments}
        newly_assigned_count = len(valid_student_ids) - len(already_assigned_ids)
        already_assigned_count = len(already_assigned_ids)

        # 4. Upsert StageAssignments with status='SHORTLISTED' (qualified)
        await self.assignment_repo.upsert_assignments(
            stage_id=stage_id,
            drive_id=drive_id,
            student_ids=valid_student_ids,
            status="SHORTLISTED",
        )

        # 5. Automatically publish stage if not published
        if not stage.is_published:
            stage.is_published = True
            self.session.add(stage)

        # 6. Update DriveRegistration status to 'SHORTLISTED' for newly shortlisted students
        stmt_update_reg = (
            update(DriveRegistration)
            .where(
                DriveRegistration.drive_id == drive_id,
                DriveRegistration.student_user_id.in_(valid_student_ids),
                DriveRegistration.status == "REGISTERED",
            )
            .values(status="SHORTLISTED")
        )
        await self.session.execute(stmt_update_reg)

        # 7. Audit Log Record
        audit_log = AuditLog(
            performed_by_user_id=current_user_id,
            action="STAGE_QUALIFIED_IMPORT_CONFIRMED",
            entity_type="STAGE",
            entity_id=stage.id,
            new_state={
                "drive_id": str(drive_id),
                "stage_id": str(stage_id),
                "stage_name": stage.name,
                "stage_sequence": stage.sequence_order,
                "filename": request.filename,
                "total_submitted": len(request.student_ids),
                "total_confirmed": len(valid_student_ids),
                "newly_assigned_count": newly_assigned_count,
                "already_assigned_count": already_assigned_count,
            },
        )
        self.audit_repo.add(audit_log)
        await self.session.commit()

        # 8. Post-commit Notification Dispatch
        if self.dispatcher:
            try:
                items = [
                    {
                        "user_id": sid,
                        "title": f"Qualified: {stage.name}",
                        "body": f"Congratulations! You have qualified for {stage.name} in {drive.title}.",
                        "notification_type": "SHORTLISTED",
                        "reference_id": stage.id,
                        "reference_type": "PLACEMENT_STAGE",
                        "send_push": True,
                    }
                    for sid in valid_student_ids
                ]
                await self.dispatcher.dispatch_bulk_notifications(items)
            except Exception as e:
                logger.error("Failed to dispatch notifications for stage %s: %s", stage.id, e)

        return StageImportConfirmResponse(
            drive_id=drive_id,
            stage_id=stage_id,
            stage_name=stage.name,
            total_submitted=len(request.student_ids),
            newly_assigned_count=newly_assigned_count,
            already_assigned_count=already_assigned_count,
            message=f"Successfully updated {stage.name}: {len(valid_student_ids)} students qualified ({newly_assigned_count} newly qualified, {already_assigned_count} updated).",
        )

    async def list_stage_qualified_students(
        self,
        drive_id: UUID,
        stage_id: UUID,
    ) -> list[StageQualifiedStudentItem]:
        """
        Returns all students assigned/qualified for this specific drive stage.
        """
        stmt = (
            select(StageAssignment, StudentProfile, User)
            .join(StudentProfile, StageAssignment.student_user_id == StudentProfile.user_id)
            .join(User, StageAssignment.student_user_id == User.id)
            .where(
                StageAssignment.drive_id == drive_id,
                StageAssignment.stage_id == stage_id,
            )
            .order_by(StudentProfile.roll_number.asc())
        )
        rows = (await self.session.execute(stmt)).all()

        return [
            StageQualifiedStudentItem(
                assignment_id=assignment.id,
                stage_id=assignment.stage_id,
                student_user_id=assignment.student_user_id,
                roll_number=profile.roll_number,
                full_name=user.full_name or f"Student {profile.roll_number}",
                email=user.email,
                branch_code=profile.branch_code,
                cgpa=profile.cgpa,
                status=assignment.status,
                assigned_at=assignment.assigned_at,
            )
            for assignment, profile, user in rows
        ]
