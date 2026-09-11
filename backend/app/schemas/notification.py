"""
Notification schemas.
"""
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class NotificationResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    body: str
    notification_type: str
    reference_id: UUID | None = None
    reference_type: str | None = None
    is_read: bool
    push_sent: bool
    push_sent_at: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationTaskPayload(BaseModel):
    """Payload sent via Cloud Tasks to /internal/tasks/send-notification."""
    user_id: UUID
    notification_type: str = Field(..., max_length=50)
    title: str = Field(..., max_length=255)
    body: str
    reference_id: UUID | None = None
    reference_type: str | None = Field(None, max_length=50)
    send_push: bool = True
    idempotency_key: str | None = None

    model_config = ConfigDict(extra="ignore")


class NotificationTaskResponse(BaseModel):
    """Response returned by /internal/tasks/send-notification."""
    status: Literal["processed", "skipped"]
    notification_id: UUID | None = None
    reason: str | None = None

