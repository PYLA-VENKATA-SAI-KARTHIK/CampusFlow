"""
CampusFlow — Notification Worker Service

Processes background notification tasks dispatched via Cloud Tasks.
- Enforces strict deduplication & idempotency on (user_id, notification_type, reference_id).
- Writes the in-app Notification database record.
- Operates independently from the frontend request path.
"""
from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification
from app.repositories.drive_registration_repository import DriveRegistrationRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.push_subscription_repository import PushSubscriptionRepository
from app.schemas.notification import NotificationTaskPayload, NotificationTaskResponse
from app.services.push_sender_service import PushSenderService, get_push_sender_service

logger = logging.getLogger(__name__)

DEADLINE_REMINDER_TYPES = {"DEADLINE_REMINDER_24H", "DEADLINE_REMINDER_6H", "DEADLINE_REMINDER_1H"}


class NotificationWorkerService:
    """Service handling asynchronous notification processing, in-app DB persistence, and Web Push delivery."""

    def __init__(
        self,
        notification_repo: NotificationRepository,
        session: AsyncSession,
        registration_repo: DriveRegistrationRepository | None = None,
        push_repo: PushSubscriptionRepository | None = None,
        push_sender: PushSenderService | None = None,
    ) -> None:
        self.notification_repo = notification_repo
        self.session = session
        self.registration_repo = registration_repo or DriveRegistrationRepository(session=session)
        self.push_repo = push_repo or PushSubscriptionRepository(session=session)
        self.push_sender = push_sender or get_push_sender_service()

    async def process_notification_task(
        self,
        task: NotificationTaskPayload,
    ) -> NotificationTaskResponse:
        """
        Process an incoming notification task idempotently.
        If a matching notification already exists for this (user_id, notification_type, reference_id),
        the task is skipped without creating a duplicate.
        For deadline reminder tasks, re-checks if the student has already registered.
        After in-app record is committed, dispatches Web Push notifications to all active device subscriptions.
        """
        # 0. Re-check registration for deadline reminder tasks
        if task.notification_type in DEADLINE_REMINDER_TYPES and task.reference_id:
            registration = await self.registration_repo.get_by_drive_and_student(
                drive_id=task.reference_id,
                student_user_id=task.user_id,
            )
            if registration and registration.status == "REGISTERED":
                logger.info(
                    "Skipping deadline reminder for user %s on drive %s: already registered",
                    task.user_id,
                    task.reference_id,
                )
                return NotificationTaskResponse(
                    status="skipped",
                    reason="already_registered",
                )

        # 1. Pre-check: Look up existing notification by deduplication key
        existing = await self.notification_repo.get_by_dedup(
            user_id=task.user_id,
            notification_type=task.notification_type,
            reference_id=task.reference_id,
        )

        if existing:
            logger.info(
                "Skipping duplicate notification task for user %s (type=%s, ref=%s)",
                task.user_id,
                task.notification_type,
                task.reference_id,
            )
            return NotificationTaskResponse(
                status="skipped",
                notification_id=existing.id,
                reason="idempotent_duplicate",
            )

        # 2. Create the in-app notification database record (safe under race conditions)
        notification = Notification(
            user_id=task.user_id,
            title=task.title,
            body=task.body,
            notification_type=task.notification_type,
            reference_id=task.reference_id,
            reference_type=task.reference_type,
            is_read=False,
            push_sent=False,
        )

        try:
            created_notification = await self.notification_repo.create_notification(notification)
            await self.session.commit()

            logger.info(
                "Created in-app notification %s for user %s (type=%s)",
                created_notification.id,
                task.user_id,
                task.notification_type,
            )

            # 3. Deliver Web Push to active subscriptions (post-commit, failure isolated)
            if task.send_push and self.push_sender:
                try:
                    active_subs = await self.push_repo.get_active_subscriptions_for_user(task.user_id)
                    if active_subs:
                        success_count = 0
                        push_payload = {
                            "title": task.title,
                            "body": task.body,
                            "notification_type": task.notification_type,
                            "reference_id": str(task.reference_id) if task.reference_id else None,
                            "reference_type": task.reference_type,
                            "notification_id": str(created_notification.id),
                            "data": {
                                "url": f"/drives/{task.reference_id}" if task.reference_id else "/notifications",
                                "notification_id": str(created_notification.id),
                            },
                        }
                        for sub in active_subs:
                            try:
                                result = await self.push_sender.send_notification(
                                    subscription=sub,
                                    payload=push_payload,
                                )
                                if result.status == "success":
                                    await self.push_repo.mark_subscription_used(sub.id)
                                    success_count += 1
                                elif result.status == "expired":
                                    # HTTP 410 / 404: Subscription expired or unregistered
                                    await self.push_repo.mark_subscription_inactive(sub.id)
                                    logger.info(
                                        "Marked expired push subscription %s as inactive (status=%s)",
                                        sub.id,
                                        result.status_code,
                                    )
                                else:
                                    logger.warning(
                                        "Push delivery failed for subscription %s: %s",
                                        sub.id,
                                        result.error_message,
                                    )
                            except Exception as sub_err:
                                logger.error(
                                    "Error delivering push to subscription %s: %s",
                                    sub.id,
                                    sub_err,
                                )

                        if success_count > 0:
                            await self.notification_repo.mark_push_sent(created_notification.id)

                        await self.session.commit()
                except Exception as push_err:
                    logger.error(
                        "Failed to process push notifications for notification %s: %s",
                        created_notification.id,
                        push_err,
                    )

            return NotificationTaskResponse(
                status="processed",
                notification_id=created_notification.id,
            )
        except IntegrityError:
            await self.session.rollback()
            existing = await self.notification_repo.get_by_dedup(
                user_id=task.user_id,
                notification_type=task.notification_type,
                reference_id=task.reference_id,
            )
            logger.info(
                "Concurrent duplicate notification caught for user %s (type=%s)",
                task.user_id,
                task.notification_type,
            )
            return NotificationTaskResponse(
                status="skipped",
                notification_id=existing.id if existing else None,
                reason="idempotent_duplicate",
            )


