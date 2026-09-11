"""
Manual Broadcast schemas.
"""
from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class ManualBroadcastRequest(BaseModel):
    """Request payload for manual placement drive notification broadcast."""
    audience: Literal["ELIGIBLE", "REGISTERED", "SHORTLISTED"] = Field(
        ...,
        description="Target audience category for the notification broadcast",
    )
    title: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Notification title",
    )
    body: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Notification body/message content",
    )

    model_config = ConfigDict(extra="ignore")


class ManualBroadcastResponse(BaseModel):
    """Response returned upon accepting a manual broadcast request."""
    message: str
    recipient_count: int

    model_config = ConfigDict(extra="ignore")
