"""
Placement Stage service.
"""
import logging
from typing import Sequence
from uuid import UUID

from fastapi import HTTPException

from app.models.audit_log import AuditLog
from app.models.placement_stage import PlacementStage
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.placement_drive_repository import PlacementDriveRepository
from app.repositories.placement_stage_repository import PlacementStageRepository
from app.repositories.stage_assignment_repository import StageAssignmentRepository
from app.repositories.drive_registration_repository import DriveRegistrationRepository
from app.schemas.placement_stage import PlacementStageCreate, PlacementStageUpdate
from app.schemas.stage_assignment import (
    BulkStageStatusRequest,
    StageAssignmentUpdate,
    StageShortlistRequest,
)
from app.services.notification_dispatcher import NotificationDispatcher

logger = logging.getLogger(__name__)


class PlacementStageService:
    def __init__(
        self,
        stage_repo: PlacementStageRepository,
        assignment_repo: StageAssignmentRepository,
        drive_repo: PlacementDriveRepository,
        audit_repo: AuditLogRepository,
        registration_repo: DriveRegistrationRepository = None,
        dispatcher: NotificationDispatcher | None = None,
    ):
        self.stage_repo = stage_repo
        self.assignment_repo = assignment_repo
        self.drive_repo = drive_repo
        self.audit_repo = audit_repo
        self.registration_repo = registration_repo
        self.dispatcher = dispatcher


    async def _get_drive_or_404(self, drive_id: UUID):
        drive = await self.drive_repo.get_by_id(drive_id)
        if not drive:
            raise HTTPException(status_code=404, detail="Drive not found")
        return drive

    async def _get_stage_or_404(self, drive_id: UUID, stage_id: UUID) -> PlacementStage:
        stage = await self.stage_repo.get_by_id(stage_id)
        if not stage or stage.drive_id != drive_id:
            raise HTTPException(status_code=404, detail="Stage not found")
        return stage

    async def create_stage(self, drive_id: UUID, data: PlacementStageCreate, user_id: UUID) -> PlacementStage:
        await self._get_drive_or_404(drive_id)

        # Check for duplicate sequence order
        existing_stages = await self.stage_repo.list_by_drive_id(drive_id)
        if any(s.sequence_order == data.sequence_order for s in existing_stages):
            raise HTTPException(status_code=409, detail="Stage with this sequence_order already exists")

        stage = PlacementStage(
            drive_id=drive_id,
            name=data.name,
            stage_type=data.stage_type,
            sequence_order=data.sequence_order,
            scheduled_at=data.scheduled_at,
            location_or_link=data.location_or_link,
            instructions=data.instructions,
            is_published=False,
        )

        stage = await self.stage_repo.create(stage)

        audit = AuditLog(
            performed_by_user_id=user_id,
            action="STAGE_CREATED",
            entity_type="STAGE",
            entity_id=stage.id,
            new_state={"id": str(stage.id), "name": stage.name, "sequence_order": stage.sequence_order},
        )
        self.audit_repo.add(audit)
        await self.audit_repo.session.commit()

        return stage

    async def list_stages(self, drive_id: UUID, user_id: UUID, is_student: bool) -> Sequence[PlacementStage]:
        await self._get_drive_or_404(drive_id)
        stages = await self.stage_repo.list_by_drive_id(drive_id)

        if not is_student:
            return stages

        # Student visibility filtering
        visible_stages = []
        for stage in stages:
            if not stage.is_published:
                continue
            assignment = await self.assignment_repo.get_assignment(stage.id, user_id)
            if assignment:
                visible_stages.append(stage)
        
        return visible_stages

    async def update_stage(self, drive_id: UUID, stage_id: UUID, data: PlacementStageUpdate, user_id: UUID) -> PlacementStage:
        stage = await self._get_stage_or_404(drive_id, stage_id)
        
        if data.sequence_order is not None and data.sequence_order != stage.sequence_order:
            existing_stages = await self.stage_repo.list_by_drive_id(drive_id)
            if any(s.sequence_order == data.sequence_order and s.id != stage.id for s in existing_stages):
                raise HTTPException(status_code=409, detail="Stage with this sequence_order already exists")

        old_state = {"name": stage.name, "sequence_order": stage.sequence_order, "scheduled_at": stage.scheduled_at.isoformat() if stage.scheduled_at else None}
        
        stage = await self.stage_repo.update(stage, data)

        audit = AuditLog(
            performed_by_user_id=user_id,
            action="STAGE_UPDATED",
            entity_type="STAGE",
            entity_id=stage.id,
            old_state=old_state,
            new_state={"name": stage.name, "sequence_order": stage.sequence_order, "scheduled_at": stage.scheduled_at.isoformat() if stage.scheduled_at else None},
        )
        self.audit_repo.add(audit)
        await self.audit_repo.session.commit()

        # Post-commit notification dispatch: STAGE_UPDATED (if stage is published)
        if stage.is_published and self.dispatcher:
            try:
                assignments = await self.assignment_repo.list_assignments_for_stage(stage.id)
                if assignments:
                    items = [
                        {
                            "user_id": a.student_user_id,
                            "title": f"Stage Schedule Updated: {stage.name}",
                            "body": f"The schedule or details for {stage.name} have been updated. Check the stage instructions.",
                            "notification_type": "STAGE_UPDATED",
                            "reference_id": stage.id,
                            "reference_type": "PLACEMENT_STAGE",
                            "send_push": True,
                        }
                        for a in assignments
                    ]
                    await self.dispatcher.dispatch_bulk_notifications(items)
            except Exception as e:
                logger.error("Failed to dispatch STAGE_UPDATED notifications for stage %s: %s", stage.id, e)

        return stage

    async def publish_stage(self, drive_id: UUID, stage_id: UUID, user_id: UUID) -> dict:
        stage = await self._get_stage_or_404(drive_id, stage_id)
        if stage.is_published:
            return {"message": "Stage already published"}

        stage = await self.stage_repo.publish(stage)

        audit = AuditLog(
            performed_by_user_id=user_id,
            action="STAGE_PUBLISHED",
            entity_type="STAGE",
            entity_id=stage.id,
        )
        self.audit_repo.add(audit)
        await self.audit_repo.session.commit()

        return {"message": "Stage published"}

    async def shortlist_students(self, drive_id: UUID, stage_id: UUID, data: StageShortlistRequest, user_id: UUID) -> dict:
        drive = await self._get_drive_or_404(drive_id)
        stage = await self._get_stage_or_404(drive_id, stage_id)
        
        # Deduplicate student IDs
        unique_student_ids = list(dict.fromkeys(data.student_ids))

        # Verify all students are registered using targeted SQL query
        registered_student_ids = await self.registration_repo.get_registered_student_ids_for_drive_and_students(
            drive_id, unique_student_ids
        )
        
        for student_id in unique_student_ids:
            if student_id not in registered_student_ids:
                raise HTTPException(status_code=422, detail=f"Student {student_id} is not registered for this drive")

        # Upsert assignments
        await self.assignment_repo.upsert_assignments(stage_id, drive_id, unique_student_ids, status="SHORTLISTED")
        
        # Audit Log
        audit = AuditLog(
            performed_by_user_id=user_id,
            action="STUDENTS_SHORTLISTED",
            entity_type="STAGE",
            entity_id=stage.id,
            new_state={"student_ids": [str(sid) for sid in unique_student_ids]}
        )
        self.audit_repo.add(audit)
        await self.audit_repo.session.commit()
        
        # Post-commit notification dispatch: SHORTLISTED
        if self.dispatcher:
            try:
                items = [
                    {
                        "user_id": student_id,
                        "title": f"Shortlisted: {stage.name}",
                        "body": f"You have been shortlisted for {stage.name} in {drive.title}.",
                        "notification_type": "SHORTLISTED",
                        "reference_id": stage.id,
                        "reference_type": "PLACEMENT_STAGE",
                        "send_push": True,
                    }
                    for student_id in unique_student_ids
                ]
                await self.dispatcher.dispatch_bulk_notifications(items)
            except Exception as e:
                logger.error("Failed to dispatch SHORTLISTED notifications for stage %s: %s", stage.id, e)

        return {"message": f"{len(unique_student_ids)} students shortlisted"}

    async def bulk_update_status(
        self,
        drive_id: UUID,
        stage_id: UUID,
        data: BulkStageStatusRequest,
        user_id: UUID,
    ) -> dict:
        await self._get_drive_or_404(drive_id)
        stage = await self._get_stage_or_404(drive_id, stage_id)

        # Deduplicate student IDs
        unique_student_ids = list(dict.fromkeys(data.student_ids))

        # Verify all students are assigned to this stage
        assignments = await self.assignment_repo.list_assignments_for_stage_and_students(
            stage_id, unique_student_ids
        )
        assigned_student_ids = {a.student_user_id for a in assignments}

        for student_id in unique_student_ids:
            if student_id not in assigned_student_ids:
                raise HTTPException(
                    status_code=422,
                    detail=f"Student {student_id} is not assigned to this stage",
                )

        # Bulk update in database
        await self.assignment_repo.bulk_update_assignments_status(
            stage_id=stage_id,
            student_ids=unique_student_ids,
            status=data.status,
            result_notes=data.result_notes,
        )

        # Audit Log
        audit = AuditLog(
            performed_by_user_id=user_id,
            action="STAGE_ASSIGNMENTS_BULK_UPDATED",
            entity_type="STAGE",
            entity_id=stage.id,
            new_state={
                "status": data.status,
                "result_notes": data.result_notes,
                "student_ids": [str(sid) for sid in unique_student_ids],
                "count": len(unique_student_ids),
            },
        )
        self.audit_repo.add(audit)
        await self.audit_repo.session.commit()

        return {
            "message": f"{len(unique_student_ids)} candidate assignments updated to {data.status}"
        }

    async def update_assignment(self, drive_id: UUID, stage_id: UUID, student_id: UUID, data: StageAssignmentUpdate, user_id: UUID):
        await self._get_stage_or_404(drive_id, stage_id)
        
        assignment = await self.assignment_repo.get_assignment(stage_id, student_id)
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")
            
        old_state = {"status": assignment.status, "result_notes": assignment.result_notes}
        
        assignment = await self.assignment_repo.update_assignment(assignment, data.model_dump(exclude_unset=True))
        
        audit = AuditLog(
            performed_by_user_id=user_id,
            action="STAGE_ASSIGNMENT_UPDATED",
            entity_type="STAGE_ASSIGNMENT",
            entity_id=assignment.id,
            old_state=old_state,
            new_state={"status": assignment.status, "result_notes": assignment.result_notes}
        )
        self.audit_repo.add(audit)
        await self.audit_repo.session.commit()
        
        return assignment

    async def publish_results(self, drive_id: UUID, stage_id: UUID, user_id: UUID) -> dict:
        drive = await self._get_drive_or_404(drive_id)
        stage = await self._get_stage_or_404(drive_id, stage_id)
        
        assignments = await self.assignment_repo.list_assignments_for_stage(stage_id)
        
        audit = AuditLog(
            performed_by_user_id=user_id,
            action="STAGE_RESULTS_PUBLISHED",
            entity_type="STAGE",
            entity_id=stage.id
        )
        self.audit_repo.add(audit)
        await self.audit_repo.session.commit()
        
        # Post-commit notification dispatch: RESULT_PUBLISHED
        if self.dispatcher:
            try:
                items = [
                    {
                        "user_id": a.student_user_id,
                        "title": f"Stage Results Published: {stage.name}",
                        "body": f"Results for {stage.name} in {drive.title} have been published.",
                        "notification_type": "RESULT_PUBLISHED",
                        "reference_id": stage.id,
                        "reference_type": "PLACEMENT_STAGE",
                        "send_push": True,
                    }
                    for a in assignments
                ]
                await self.dispatcher.dispatch_bulk_notifications(items)
            except Exception as e:
                logger.error("Failed to dispatch RESULT_PUBLISHED notifications for stage %s: %s", stage.id, e)

        return {"message": "Results published and notifications generated"}

