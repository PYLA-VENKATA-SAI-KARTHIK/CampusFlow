"""
Placement Drive service.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Sequence
from uuid import UUID

from fastapi import HTTPException, status
import logging
from app.models.audit_log import AuditLog

from app.models.eligibility_criteria import EligibilityCriteria
from app.models.placement_drive import PlacementDrive
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.drive_registration_repository import DriveRegistrationRepository
from app.repositories.placement_drive_repository import PlacementDriveRepository
from app.repositories.placement_stage_repository import PlacementStageRepository
from app.repositories.stage_assignment_repository import StageAssignmentRepository
from app.repositories.student_profile_repository import StudentProfileRepository
from app.schemas.manual_broadcast import ManualBroadcastRequest, ManualBroadcastResponse
from app.services.eligibility_service import EligibilityService
from app.services.notification_dispatcher import NotificationDispatcher
from app.schemas.placement_drive import (
    DriveStatus,
    EligibilityResult,
    PlacementDriveCreate,
    PlacementDriveStatusUpdate,
    PlacementDriveUpdate,
)

logger = logging.getLogger(__name__)

VALID_TRANSITIONS: dict[str, list[str]] = {
    "DRAFT": ["PUBLISHED"],
    "PUBLISHED": ["REGISTRATION_OPEN"],
    "REGISTRATION_OPEN": ["REGISTRATION_CLOSED"],
    "REGISTRATION_CLOSED": ["SHORTLISTING"],
    "SHORTLISTING": ["ASSESSMENT"],
    "ASSESSMENT": ["INTERVIEW"],
    "INTERVIEW": ["RESULT"],
    "RESULT": ["COMPLETED"],
    "COMPLETED": [],
}


class PlacementDriveService:
    def __init__(
        self,
        drive_repo: PlacementDriveRepository,
        audit_repo: AuditLogRepository,
        student_repo: StudentProfileRepository,
        dispatcher: NotificationDispatcher | None = None,
        reg_repo: DriveRegistrationRepository | None = None,
        stage_repo: PlacementStageRepository | None = None,
        assignment_repo: StageAssignmentRepository | None = None,
    ) -> None:
        self.drive_repo = drive_repo
        self.audit_repo = audit_repo
        self.student_repo = student_repo
        self.dispatcher = dispatcher
        self.reg_repo = reg_repo or DriveRegistrationRepository(drive_repo.session)
        self.stage_repo = stage_repo or PlacementStageRepository(drive_repo.session)
        self.assignment_repo = assignment_repo or StageAssignmentRepository(drive_repo.session)


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
            entity_type="DRIVE",
            entity_id=entity_id,
            old_state=old_state,
            new_state=new_state,
        )
        self.audit_repo.add(audit_log)

    async def create_drive(self, data: PlacementDriveCreate, user_id: UUID | str) -> PlacementDrive:
        if isinstance(user_id, str):
            user_id = UUID(user_id)

        drive = PlacementDrive(
            company_id=data.company_id,
            title=data.title,
            job_role=data.job_role,
            description=data.description,
            ctc_lpa=data.ctc_lpa,
            stipend_monthly=data.stipend_monthly,
            location=data.location,
            bond_details=data.bond_details,
            registration_deadline=data.registration_deadline,
            status="DRAFT",
            created_by_user_id=user_id,
        )
        self.drive_repo.add(drive)
        
        # Flushed to get drive ID by SQLAlchemy session later, or we can use UUID explicitly if set
        # Since we mapped default=uuid4, drive.id is not populated until flush unless we do it:
        if not drive.id:
            drive.id = __import__("uuid").uuid4()

        criteria = EligibilityCriteria(
            drive_id=drive.id,
            criteria=data.eligibility_criteria.model_dump(mode="json", exclude_none=True)
        )
        self.drive_repo.add_criteria(criteria)
        drive.eligibility_criteria = criteria # Attach for response

        self._log_audit(
            user_id=user_id,
            action="DRIVE_CREATED",
            entity_id=drive.id,
            new_state={"status": "DRAFT", "title": data.title}
        )

        await self.drive_repo.session.commit()
        return await self.get_drive(drive.id)

    async def get_drive(self, drive_id: UUID, current_user_id: UUID | None = None, is_student: bool = False) -> PlacementDrive:
        drive = await self.drive_repo.get_by_id(drive_id)
        if not drive:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Placement drive with id '{drive_id}' not found."
            )
            
        if is_student and current_user_id:
            profile = await self.student_repo.get_by_user_id(current_user_id)
            if profile and drive.eligibility_criteria:
                is_eligible, reasons = EligibilityService.evaluate(profile, drive.eligibility_criteria.criteria)
                drive.my_eligibility = EligibilityResult(is_eligible=is_eligible, reasons=reasons)
            else:
                drive.my_eligibility = EligibilityResult(is_eligible=False, reasons=["Student profile not found."])
            
            existing_reg = await self.reg_repo.get_by_drive_and_student(drive_id, current_user_id)
            drive.is_registered = existing_reg is not None
                
        return drive

    async def list_drives(
        self, status: str | None = None, skip: int = 0, limit: int = 20, is_student: bool = False
    ) -> tuple[Sequence[PlacementDrive], int]:
        if is_student and status == "DRAFT":
            return [], 0
        return await self.drive_repo.list_drives(
            status=status, skip=skip, limit=limit, exclude_draft=is_student
        )

    async def update_drive(
        self, drive_id: UUID, data: PlacementDriveUpdate, user_id: UUID | str
    ) -> PlacementDrive:
        if isinstance(user_id, str):
            user_id = UUID(user_id)

        drive = await self.get_drive(drive_id)

        if drive.status != "DRAFT":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Drives can only be updated while in DRAFT status."
            )

        old_state = {"title": drive.title, "ctc_lpa": float(drive.ctc_lpa) if drive.ctc_lpa else None}
        
        # Update drive fields
        update_data = data.model_dump(exclude_unset=True)
        criteria_update = update_data.pop("eligibility_criteria", None)
        
        for key, value in update_data.items():
            setattr(drive, key, value)
            
        if criteria_update and drive.eligibility_criteria:
            # Simple replace for Phase 2.1
            drive.eligibility_criteria.criteria = criteria_update

        new_state = {"title": drive.title, "ctc_lpa": float(drive.ctc_lpa) if drive.ctc_lpa else None}

        self._log_audit(
            user_id=user_id,
            action="DRIVE_UPDATED",
            entity_id=drive.id,
            old_state=old_state,
            new_state=new_state
        )

        await self.drive_repo.session.commit()
        return await self.get_drive(drive.id)

    async def update_drive_status(
        self, drive_id: UUID, data: PlacementDriveStatusUpdate, user_id: UUID | str
    ) -> PlacementDrive:
        if isinstance(user_id, str):
            user_id = UUID(user_id)

        drive = await self.get_drive(drive_id)
        current_status = drive.status
        new_status = data.status

        if current_status == new_status:
            return drive

        allowed_next = VALID_TRANSITIONS.get(current_status, [])
        if new_status not in allowed_next:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Invalid lifecycle transition from {current_status} to {new_status}."
            )

        # Precondition: REGISTRATION_OPEN requires registration_deadline to be set
        if new_status == "REGISTRATION_OPEN" and drive.registration_deadline is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Cannot open registration: registration_deadline must be set before opening registration."
            )

        # Precondition: ASSESSMENT requires at least one placement stage to exist
        if new_status == "ASSESSMENT":
            stage_count = await self.drive_repo.count_stages(drive_id)
            if stage_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Cannot advance to ASSESSMENT: at least one placement stage must exist for this drive."
                )

        old_state = {"status": current_status}
        
        drive.status = new_status
        if new_status == "PUBLISHED" and not drive.published_at:
            drive.published_at = datetime.now(timezone.utc)

        self._log_audit(
            user_id=user_id,
            action=f"DRIVE_{new_status}",
            entity_id=drive.id,
            old_state=old_state,
            new_state={"status": new_status}
        )

        await self.drive_repo.session.commit()

        # Post-commit notification dispatch: DRAFT -> PUBLISHED
        if current_status == "DRAFT" and new_status == "PUBLISHED" and self.dispatcher:
            try:
                active_profiles = await self.student_repo.list_all_active_profiles()
                criteria_dict = drive.eligibility_criteria.criteria if drive.eligibility_criteria else {}
                company_name = drive.company.name if drive.company else "A company"
                items = []
                for profile in active_profiles:
                    is_eligible, _ = EligibilityService.evaluate(profile, criteria_dict)
                    if is_eligible:
                        items.append({
                            "user_id": profile.user_id,
                            "title": f"New Placement Drive: {drive.title}",
                            "body": f"{company_name} is hiring for {drive.job_role}. Check your eligibility and register before the deadline.",
                            "notification_type": "DRIVE_PUBLISHED",
                            "reference_id": drive.id,
                            "reference_type": "DRIVE",
                            "send_push": True,
                        })
                if items:
                    await self.dispatcher.dispatch_bulk_notifications(items)
            except Exception as e:
                logger.error("Failed to dispatch DRIVE_PUBLISHED notifications for drive %s: %s", drive.id, e)

        return await self.get_drive(drive.id)


    async def check_eligibility(self, drive_id: UUID, user_id: UUID | str) -> EligibilityResult:
        if isinstance(user_id, str):
            user_id = UUID(user_id)
            
        drive = await self.get_drive(drive_id)
        profile = await self.student_repo.get_by_user_id(user_id)
        
        if not profile:
            return EligibilityResult(is_eligible=False, reasons=["Student profile not found."])
            
        if not drive.eligibility_criteria:
            return EligibilityResult(is_eligible=True, reasons=[])
            
        is_eligible, reasons = EligibilityService.evaluate(profile, drive.eligibility_criteria.criteria)
        return EligibilityResult(is_eligible=is_eligible, reasons=reasons)
        
    async def list_eligible_students(self, drive_id: UUID, skip: int = 0, limit: int = 20) -> tuple[list, int]:
        drive = await self.get_drive(drive_id)
        criteria = drive.eligibility_criteria.criteria if drive.eligibility_criteria else {}
        
        all_profiles, _ = await self.student_repo.list_students(skip=0, limit=100000)
        
        eligible_profiles = []
        for profile in all_profiles:
            is_eligible, _ = EligibilityService.evaluate(profile, criteria)
            if is_eligible:
                eligible_profiles.append(profile)
                
        total = len(eligible_profiles)
        paged_profiles = eligible_profiles[skip: skip + limit]
        return paged_profiles, total

    async def broadcast_notification(
        self,
        drive_id: UUID,
        data: ManualBroadcastRequest,
        user_id: UUID | str,
    ) -> ManualBroadcastResponse:
        """
        Manually broadcast notifications to students for a drive based on selected audience.
        - ELIGIBLE: Active students passing eligibility criteria.
        - REGISTERED: Students with status='REGISTERED'.
        - SHORTLISTED: Students assigned to the latest published stage with status SHORTLISTED or SELECTED.
        """
        if isinstance(user_id, str):
            user_id = UUID(user_id)

        drive = await self.get_drive(drive_id)

        recipient_user_ids: list[UUID] = []

        if data.audience == "ELIGIBLE":
            active_profiles = await self.student_repo.list_all_active_profiles()
            criteria_dict = drive.eligibility_criteria.criteria if drive.eligibility_criteria else {}
            for profile in active_profiles:
                is_eligible, _ = EligibilityService.evaluate(profile, criteria_dict)
                if is_eligible:
                    recipient_user_ids.append(profile.user_id)

        elif data.audience == "REGISTERED":
            registered_ids = await self.reg_repo.get_registered_student_ids_for_drive(drive_id)
            recipient_user_ids = list(registered_ids)

        elif data.audience == "SHORTLISTED":
            stages = await self.stage_repo.list_by_drive_id(drive_id)
            published_stages = [s for s in stages if s.is_published]
            if published_stages:
                latest_stage = published_stages[-1]
                assignments = await self.assignment_repo.list_assignments_for_stage(latest_stage.id)
                for a in assignments:
                    if a.status in ("SHORTLISTED", "SELECTED"):
                        recipient_user_ids.append(a.student_user_id)

        recipient_count = len(recipient_user_ids)

        # Audit log creation
        self._log_audit(
            user_id=user_id,
            action="MANUAL_NOTIFICATION_SENT",
            entity_id=drive.id,
            new_state={
                "audience": data.audience,
                "recipient_count": recipient_count,
                "title": data.title,
            },
        )
        await self.drive_repo.session.commit()

        # Enqueue async tasks if recipients exist
        if recipient_count > 0 and self.dispatcher:
            items = [
                {
                    "user_id": uid,
                    "title": data.title,
                    "body": data.body,
                    "notification_type": "MANUAL_BROADCAST",
                    "reference_id": drive.id,
                    "reference_type": "DRIVE",
                    "send_push": True,
                }
                for uid in recipient_user_ids
            ]
            try:
                await self.dispatcher.dispatch_bulk_notifications(items)
            except Exception as e:
                logger.error("Failed to enqueue manual broadcast tasks for drive %s: %s", drive.id, e)

        return ManualBroadcastResponse(
            message=f"Notification enqueued for {recipient_count} students",
            recipient_count=recipient_count,
        )

