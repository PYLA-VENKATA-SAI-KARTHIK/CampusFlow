from datetime import datetime, timezone
import logging
from typing import Sequence
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.models.audit_log import AuditLog
from app.models.drive_registration import DriveRegistration
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.drive_registration_repository import DriveRegistrationRepository
from app.repositories.placement_drive_repository import PlacementDriveRepository
from app.repositories.student_profile_repository import StudentProfileRepository
from app.schemas.drive_registration import (
    CurrentStageSummary,
    DriveRegistrationResponse,
    DriveRegistrationWithStudentResponse,
    RegistrationStageSummary,
    RegistrationStudentSummary,
    StudentApplicationResponse
)
from app.services.placement_drive_service import PlacementDriveService
from app.repositories.stage_assignment_repository import StageAssignmentRepository
from app.services.notification_dispatcher import NotificationDispatcher

logger = logging.getLogger(__name__)


class RegistrationService:
    def __init__(
        self,
        registration_repo: DriveRegistrationRepository,
        audit_repo: AuditLogRepository,
        drive_repo: PlacementDriveRepository,
        student_repo: StudentProfileRepository,
        drive_service: PlacementDriveService,
        assignment_repo: StageAssignmentRepository,
        dispatcher: NotificationDispatcher | None = None,
    ):
        self.registration_repo = registration_repo
        self.audit_repo = audit_repo
        self.drive_repo = drive_repo
        self.student_repo = student_repo
        self.drive_service = drive_service
        self.assignment_repo = assignment_repo
        self.dispatcher = dispatcher


    def _log_audit(
        self,
        user_id: UUID,
        action: str,
        entity_id: UUID,
        old_state: dict | None = None,
        new_state: dict | None = None,
    ) -> None:
        audit_log = AuditLog(
            performed_by_user_id=user_id,
            action=action,
            entity_type="REGISTRATION",
            entity_id=entity_id,
            old_state=old_state,
            new_state=new_state,
        )
        self.audit_repo.add(audit_log)

    async def register_student(self, drive_id: UUID, student_user_id: UUID) -> DriveRegistrationResponse:
        # 1. Fetch Drive
        drive = await self.drive_repo.get_by_id(drive_id)
        if not drive:
            raise HTTPException(status_code=404, detail="Placement drive not found.")
        
        if drive.status != "REGISTRATION_OPEN":
            raise HTTPException(status_code=422, detail="Drive is not open for registration.")

        if drive.registration_deadline:
            now_utc = datetime.now(timezone.utc)
            deadline = drive.registration_deadline
            if deadline.tzinfo is None:
                deadline = deadline.replace(tzinfo=timezone.utc)
            if now_utc > deadline:
                raise HTTPException(status_code=422, detail="Registration deadline has passed.")

        # 2. Check for duplicate registration
        existing = await self.registration_repo.get_by_drive_and_student(drive_id, student_user_id)
        if existing:
            raise HTTPException(status_code=409, detail="Already registered for this drive.")

        # 3. Check for resume
        student = await self.student_repo.get_by_user_id(student_user_id)
        if not student:
            raise HTTPException(status_code=404, detail="Student profile not found.")
        
        if not student.resume_gcs_path:
            raise HTTPException(status_code=400, detail="No resume uploaded on profile.")

        # 4. Check eligibility
        eligibility = await self.drive_service.check_eligibility(drive_id, student_user_id)
        if not eligibility.is_eligible:
            raise HTTPException(status_code=403, detail="Not eligible for this drive.")

        # 5. Create Registration
        registration = DriveRegistration(
            drive_id=drive_id,
            student_user_id=student_user_id,
            resume_gcs_path_at_registration=student.resume_gcs_path,
            status="REGISTERED"
        )
        
        await self.registration_repo.create(registration)
        
        # 6. Audit Log
        self._log_audit(
            user_id=student_user_id,
            action="DRIVE_REGISTERED",
            entity_id=registration.id,
            new_state={"drive_id": str(drive_id), "status": "REGISTERED"}
        )
        
        try:
            await self.registration_repo.session.commit()
            await self.registration_repo.session.refresh(registration)
        except IntegrityError:
            await self.registration_repo.session.rollback()
            raise HTTPException(status_code=409, detail="Already registered for this drive.")

        # Post-commit notification dispatch: REGISTRATION_CONFIRMED
        if self.dispatcher:
            try:
                await self.dispatcher.dispatch_notification(
                    user_id=student_user_id,
                    title=f"Registration Confirmed: {drive.title}",
                    body=f"You have successfully registered for {drive.title}. Keep track of stage announcements.",
                    notification_type="REGISTRATION_CONFIRMED",
                    reference_id=drive.id,
                    reference_type="DRIVE",
                    send_push=True,
                )
            except Exception as e:
                logger.error(
                    "Failed to dispatch REGISTRATION_CONFIRMED notification for drive %s, user %s: %s",
                    drive.id,
                    student_user_id,
                    e,
                )

        return DriveRegistrationResponse.model_validate(registration)


    async def list_drive_registrations(
        self,
        drive_id: UUID,
        skip: int = 0,
        limit: int = 20,
        status: str | None = None,
        branch: str | None = None,
        search: str | None = None,
    ) -> tuple[Sequence[DriveRegistrationWithStudentResponse], int]:
        drive = await self.drive_repo.get_by_id(drive_id)
        if not drive:
            raise HTTPException(status_code=404, detail="Placement drive not found.")
            
        rows, total = await self.registration_repo.list_by_drive_id(drive_id, skip, limit, status, branch, search)
        
        student_user_ids = [reg.student_user_id for reg, _, _ in rows]
        latest_assignments = await self.assignment_repo.get_latest_assignments_for_students_in_drive(
            drive_id, student_user_ids
        )

        result = []
        for reg, profile, user in rows:
            student_summary = RegistrationStudentSummary(
                id=profile.id,
                user_id=user.id,
                full_name=user.full_name,
                email=user.email,
                roll_number=profile.roll_number,
                branch=profile.branch_code,
                batch_year=profile.batch_year,
                cgpa=profile.cgpa,
                active_backlogs=profile.active_backlogs,
                gender=profile.gender,
                avatar_url=profile.avatar_gcs_path
            )

            stage_summary = None
            assignment = latest_assignments.get(reg.student_user_id)
            if assignment and assignment.stage:
                stage_summary = RegistrationStageSummary(
                    stage_id=assignment.stage_id,
                    stage_name=assignment.stage.name,
                    stage_type=assignment.stage.stage_type,
                    sequence_order=assignment.stage.sequence_order,
                    status=assignment.status,
                    result_notes=assignment.result_notes,
                    assigned_at=assignment.assigned_at,
                )

            response = DriveRegistrationWithStudentResponse(
                id=reg.id,
                drive_id=reg.drive_id,
                student_user_id=reg.student_user_id,
                resume_gcs_path_at_registration=reg.resume_gcs_path_at_registration,
                status=reg.status,
                registered_at=reg.registered_at,
                updated_at=reg.updated_at,
                student=student_summary,
                current_stage=stage_summary,
            )
            result.append(response)
            
        return result, total

    async def list_student_applications(self, student_user_id: UUID, skip: int = 0, limit: int = 20, status: str | None = None) -> tuple[Sequence[StudentApplicationResponse], int]:
        rows, total = await self.registration_repo.list_student_applications(student_user_id, skip, limit, status)
        
        drive_ids = [drive.id for _, drive, _ in rows]
        assignments = await self.assignment_repo.get_student_assignments_for_drives(student_user_id, drive_ids)
        assignment_map = {a.drive_id: a for a in assignments}
        
        result = []
        for reg, drive, company in rows:
            assignment = assignment_map.get(drive.id)
            current_stage = None
            if assignment:
                current_stage = CurrentStageSummary(
                    stage_name=assignment.stage.name,
                    stage_status=assignment.status,
                    scheduled_at=assignment.stage.scheduled_at
                )
                
            response = StudentApplicationResponse(
                registration_id=reg.id,
                drive_id=drive.id,
                drive_title=drive.title,
                company_name=company.name,
                company_logo_url=company.logo_gcs_path,
                registered_at=reg.registered_at,
                drive_status=drive.status,
                my_current_stage=current_stage
            )
            result.append(response)
            
        return result, total
