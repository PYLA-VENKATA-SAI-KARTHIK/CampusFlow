"""
CampusFlow — Internal Tasks Router

Provides endpoints for Cloud Tasks worker callbacks:
- POST /internal/tasks/send-notification: Processes async notification tasks and creates in-app records.

Protected by internal task authentication (Cloud Tasks OIDC / internal secret).
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.internal_auth import verify_internal_task_auth
from app.repositories.notification_repository import NotificationRepository
from app.schemas.notification import NotificationTaskPayload, NotificationTaskResponse
from app.services.notification_worker import NotificationWorkerService

logger = logging.getLogger(__name__)

router = APIRouter()


def get_notification_worker(
    session: AsyncSession = Depends(get_db),
) -> NotificationWorkerService:
    repo = NotificationRepository(session=session)
    return NotificationWorkerService(notification_repo=repo, session=session)


@router.post(
    "/send-notification",
    response_model=NotificationTaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Process Cloud Tasks notification delivery",
    description="Internal endpoint invoked by Cloud Tasks to write in-app notifications idempotently.",
)
async def send_notification_task(
    payload: NotificationTaskPayload,
    worker: NotificationWorkerService = Depends(get_notification_worker),
    _auth: dict[str, Any] = Depends(verify_internal_task_auth),
) -> NotificationTaskResponse:
    """Process an incoming Cloud Tasks notification job."""
    return await worker.process_notification_task(payload)
