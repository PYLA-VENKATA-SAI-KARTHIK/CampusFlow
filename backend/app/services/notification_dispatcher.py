"""
CampusFlow — Notification Dispatcher Service

Responsible for scheduling asynchronous notification work via Cloud Tasks.
- Accepts notification event/task data.
- Builds validated task payloads with deterministic idempotency keys.
- Enqueues tasks through the Cloud Tasks abstraction.
- Never directly performs push delivery or database writes.
"""
from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from app.schemas.notification import NotificationTaskPayload
from app.services.cloud_tasks_service import CloudTasksService, get_cloud_tasks_service

logger = logging.getLogger(__name__)


class NotificationDispatcher:
    """Service for dispatching asynchronous notification tasks to Cloud Tasks."""

    def __init__(self, cloud_tasks: CloudTasksService) -> None:
        self.cloud_tasks = cloud_tasks

    def build_idempotency_key(
        self,
        user_id: UUID,
        notification_type: str,
        reference_id: UUID | None = None,
    ) -> str:
        """Construct a stable, deterministic idempotency key for the notification."""
        ref_str = str(reference_id) if reference_id else "none"
        return f"{notification_type}:{ref_str}:{user_id}"

    async def dispatch_notification(
        self,
        user_id: UUID,
        title: str,
        body: str,
        notification_type: str,
        reference_id: UUID | None = None,
        reference_type: str | None = None,
        send_push: bool = True,
    ) -> str:
        """
        Build and enqueue a single asynchronous notification task.
        Returns the enqueued task ID / path.
        """
        idempotency_key = self.build_idempotency_key(
            user_id=user_id,
            notification_type=notification_type,
            reference_id=reference_id,
        )
        task_payload = NotificationTaskPayload(
            user_id=user_id,
            title=title,
            body=body,
            notification_type=notification_type,
            reference_id=reference_id,
            reference_type=reference_type,
            send_push=send_push,
            idempotency_key=idempotency_key,
        )

        task_dict = task_payload.model_dump(mode="json")
        task_name = f"notif-{notification_type.lower()}-{user_id}"
        
        task_id = await self.cloud_tasks.enqueue_notification_task(
            payload=task_dict,
            task_name=task_name,
        )
        logger.info(
            "Dispatched notification task %s for user %s (type=%s)",
            task_id,
            user_id,
            notification_type,
        )
        return task_id

    async def dispatch_bulk_notifications(
        self,
        items: list[dict[str, Any] | NotificationTaskPayload],
    ) -> list[str]:
        """
        Dispatch multiple notifications as individual Cloud Tasks (one task per recipient).
        Preserves fan-out reliability and individual retry isolation.
        """
        task_ids: list[str] = []
        for item in items:
            if isinstance(item, NotificationTaskPayload):
                payload = item
                if not payload.idempotency_key:
                    payload.idempotency_key = self.build_idempotency_key(
                        user_id=payload.user_id,
                        notification_type=payload.notification_type,
                        reference_id=payload.reference_id,
                    )
                task_id = await self.cloud_tasks.enqueue_notification_task(
                    payload=payload.model_dump(mode="json"),
                )
            else:
                user_id = item["user_id"]
                if isinstance(user_id, str):
                    user_id = UUID(user_id)
                ref_id = item.get("reference_id")
                if isinstance(ref_id, str):
                    ref_id = UUID(ref_id)

                task_id = await self.dispatch_notification(
                    user_id=user_id,
                    title=item["title"],
                    body=item["body"],
                    notification_type=item["notification_type"],
                    reference_id=ref_id,
                    reference_type=item.get("reference_type"),
                    send_push=item.get("send_push", True),
                )
            task_ids.append(task_id)
        return task_ids


def get_notification_dispatcher() -> NotificationDispatcher:
    """Dependency helper returning a NotificationDispatcher instance."""
    cloud_tasks = get_cloud_tasks_service()
    return NotificationDispatcher(cloud_tasks=cloud_tasks)
