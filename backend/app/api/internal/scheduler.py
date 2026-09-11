"""
CampusFlow — Internal Scheduler Router

Provides endpoints invoked periodically by Cloud Scheduler:
- POST /internal/scheduler/check-deadlines: Evaluates reminder windows and dispatches reminder tasks.
- POST /internal/scheduler/auto-close-registrations: Closes registration for drives past deadline.

Protected by internal authentication (OIDC / internal secret).
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.internal_auth import verify_internal_task_auth
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.drive_registration_repository import DriveRegistrationRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.placement_drive_repository import PlacementDriveRepository
from app.repositories.student_profile_repository import StudentProfileRepository
from app.schemas.scheduler import AutoCloseResponse, CheckDeadlinesResponse
from app.services.deadline_scheduler_service import DeadlineSchedulerService
from app.services.notification_dispatcher import NotificationDispatcher, get_notification_dispatcher

logger = logging.getLogger(__name__)

router = APIRouter()


def get_deadline_scheduler_service(
    session: AsyncSession = Depends(get_db),
    dispatcher: NotificationDispatcher = Depends(get_notification_dispatcher),
) -> DeadlineSchedulerService:
    drive_repo = PlacementDriveRepository(session=session)
    student_repo = StudentProfileRepository(session=session)
    registration_repo = DriveRegistrationRepository(session=session)
    notification_repo = NotificationRepository(session=session)
    audit_repo = AuditLogRepository(session=session)
    return DeadlineSchedulerService(
        drive_repo=drive_repo,
        student_repo=student_repo,
        registration_repo=registration_repo,
        notification_repo=notification_repo,
        audit_repo=audit_repo,
        dispatcher=dispatcher,
        session=session,
    )


@router.post(
    "/check-deadlines",
    response_model=CheckDeadlinesResponse,
    status_code=status.HTTP_200_OK,
    summary="Evaluate registration deadlines and enqueue reminders",
    description="Internal endpoint invoked by Cloud Scheduler every 30 minutes to dispatch deadline reminders.",
)
async def check_deadlines(
    service: DeadlineSchedulerService = Depends(get_deadline_scheduler_service),
    _auth: dict[str, Any] = Depends(verify_internal_task_auth),
) -> CheckDeadlinesResponse:
    """Check open drives and enqueue reminder tasks for eligible unregistered students."""
    return await service.check_deadlines()


@router.post(
    "/auto-close-registrations",
    response_model=AutoCloseResponse,
    status_code=status.HTTP_200_OK,
    summary="Auto-close registration for drives past deadline",
    description="Internal endpoint invoked by Cloud Scheduler to transition expired open drives to REGISTRATION_CLOSED.",
)
async def auto_close_registrations(
    service: DeadlineSchedulerService = Depends(get_deadline_scheduler_service),
    _auth: dict[str, Any] = Depends(verify_internal_task_auth),
) -> AutoCloseResponse:
    """Transition expired open drives to REGISTRATION_CLOSED."""
    return await service.auto_close_registrations()
