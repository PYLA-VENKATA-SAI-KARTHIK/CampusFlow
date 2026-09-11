"""
CampusFlow — Deadline Scheduler Service

Handles Cloud Scheduler background tasks:
1. check_deadlines(): Finds drives in REGISTRATION_OPEN matching 24h/6h/1h deadline windows
   and dispatches reminder Cloud Tasks to eligible, unregistered students.
2. auto_close_registrations(): Finds drives in REGISTRATION_OPEN past registration deadline
   and transitions them to REGISTRATION_CLOSED.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import logging
from typing import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.placement_drive import PlacementDrive
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.drive_registration_repository import DriveRegistrationRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.placement_drive_repository import PlacementDriveRepository
from app.repositories.student_profile_repository import StudentProfileRepository
from app.schemas.scheduler import AutoCloseResponse, CheckDeadlinesResponse
from app.services.eligibility_service import EligibilityService
from app.services.notification_dispatcher import NotificationDispatcher

logger = logging.getLogger(__name__)

# Exact 20-minute reminder windows (±10 minutes around target delta)
WINDOW_24H_MIN = timedelta(hours=23, minutes=50)
WINDOW_24H_MAX = timedelta(hours=24, minutes=10)

WINDOW_6H_MIN = timedelta(hours=5, minutes=50)
WINDOW_6H_MAX = timedelta(hours=6, minutes=10)

WINDOW_1H_MIN = timedelta(minutes=50)
WINDOW_1H_MAX = timedelta(hours=1, minutes=10)


class DeadlineSchedulerService:
    """Service for periodic deadline monitoring and automated reminder dispatching."""

    def __init__(
        self,
        drive_repo: PlacementDriveRepository,
        student_repo: StudentProfileRepository,
        registration_repo: DriveRegistrationRepository,
        notification_repo: NotificationRepository,
        audit_repo: AuditLogRepository,
        dispatcher: NotificationDispatcher,
        session: AsyncSession,
    ) -> None:
        self.drive_repo = drive_repo
        self.student_repo = student_repo
        self.registration_repo = registration_repo
        self.notification_repo = notification_repo
        self.audit_repo = audit_repo
        self.dispatcher = dispatcher
        self.session = session

    def _match_reminder_window(self, delta: timedelta) -> tuple[str | None, str | None, str | None]:
        """
        Determine if the remaining time to deadline falls into one of the 3 configured windows.
        Returns: (notification_type, title_template, body_template) or (None, None, None).
        """
        if delta < timedelta(0):
            return None, None, None

        if WINDOW_24H_MIN <= delta <= WINDOW_24H_MAX:
            return (
                "DEADLINE_REMINDER_24H",
                "Registration Deadline in 24 Hours: {title}",
                "Registration for {title} ({job_role}) closes in 24 hours. Please complete your registration if you wish to apply.",
            )
        elif WINDOW_6H_MIN <= delta <= WINDOW_6H_MAX:
            return (
                "DEADLINE_REMINDER_6H",
                "Registration Deadline in 6 Hours: {title}",
                "Only 6 hours left to register for {title} ({job_role}). Don't miss this opportunity.",
            )
        elif WINDOW_1H_MIN <= delta <= WINDOW_1H_MAX:
            return (
                "DEADLINE_REMINDER_1H",
                "Final Reminder: 1 Hour Left for {title}",
                "Registration for {title} closes in 1 hour. Submit your application now.",
            )

        return None, None, None

    async def check_deadlines(self, now: datetime | None = None) -> CheckDeadlinesResponse:
        """
        Inspect all open drives with a registration deadline.
        Enqueue Cloud Tasks reminders for eligible, unregistered students in active windows.
        """
        if now is None:
            now = datetime.now(timezone.utc)
        elif now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        open_drives = await self.drive_repo.get_open_drives_with_deadline()
        tasks_enqueued = 0

        # Lazy load active student profiles once per batch
        active_profiles = None

        for drive in open_drives:
            if not drive.registration_deadline:
                continue

            deadline = drive.registration_deadline
            if deadline.tzinfo is None:
                deadline = deadline.replace(tzinfo=timezone.utc)

            delta = deadline - now
            reminder_type, title_tpl, body_tpl = self._match_reminder_window(delta)

            if not reminder_type or not title_tpl or not body_tpl:
                continue

            if active_profiles is None:
                active_profiles = await self.student_repo.list_all_active_profiles()

            # 1. Fetch already registered students for this drive
            registered_user_ids = await self.registration_repo.get_registered_student_ids_for_drive(drive.id)

            # 2. Fetch students already notified for this specific reminder type and drive (Layer 1 dedup)
            notified_user_ids = await self.notification_repo.get_notified_user_ids(
                notification_type=reminder_type,
                reference_id=drive.id,
            )

            criteria_dict = drive.eligibility_criteria.criteria if drive.eligibility_criteria else {}
            title = title_tpl.format(title=drive.title, job_role=drive.job_role)
            body = body_tpl.format(title=drive.title, job_role=drive.job_role)

            for profile in active_profiles:
                # Exclude if already registered
                if profile.user_id in registered_user_ids:
                    continue

                # Exclude if already received this reminder
                if profile.user_id in notified_user_ids:
                    continue

                # Evaluate eligibility
                is_eligible, _ = EligibilityService.evaluate(profile, criteria_dict)
                if not is_eligible:
                    continue

                # Enqueue single task with failure isolation
                try:
                    await self.dispatcher.dispatch_notification(
                        user_id=profile.user_id,
                        title=title,
                        body=body,
                        notification_type=reminder_type,
                        reference_id=drive.id,
                        reference_type="DRIVE",
                        send_push=True,
                    )
                    tasks_enqueued += 1
                except Exception as e:
                    logger.error(
                        "Failed to dispatch %s reminder for user %s on drive %s: %s",
                        reminder_type,
                        profile.user_id,
                        drive.id,
                        e,
                    )

        logger.info(
            "Checked %d open drives, enqueued %d deadline reminder tasks",
            len(open_drives),
            tasks_enqueued,
        )
        return CheckDeadlinesResponse(
            drives_checked=len(open_drives),
            tasks_enqueued=tasks_enqueued,
        )

    async def auto_close_registrations(self, now: datetime | None = None) -> AutoCloseResponse:
        """
        Find open drives past their registration deadline and transition them to REGISTRATION_CLOSED.
        """
        if now is None:
            now = datetime.now(timezone.utc)
        elif now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        all_open_drives = await self.drive_repo.get_open_drives_with_deadline()
        drives_closed = 0

        for drive in all_open_drives:
            if not drive.registration_deadline:
                continue

            deadline = drive.registration_deadline
            if deadline.tzinfo is None:
                deadline = deadline.replace(tzinfo=timezone.utc)

            if deadline < now:
                old_status = drive.status
                drive.status = "REGISTRATION_CLOSED"

                audit_log = AuditLog(
                    performed_by_user_id=drive.created_by_user_id,
                    action="DRIVE_REGISTRATION_CLOSED",
                    entity_type="DRIVE",
                    entity_id=drive.id,
                    old_state={"status": old_status},
                    new_state={"status": "REGISTRATION_CLOSED"},
                )
                self.audit_repo.add(audit_log)
                drives_closed += 1

        if drives_closed > 0:
            await self.session.commit()

        logger.info(
            "Auto-close checked %d drives, transitioned %d to REGISTRATION_CLOSED",
            len(all_open_drives),
            drives_closed,
        )
        return AutoCloseResponse(
            drives_checked=len(all_open_drives),
            drives_closed=drives_closed,
        )
