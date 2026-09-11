"""
Push Subscription schemas.
"""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PushSubscriptionCreate(BaseModel):
    """Schema for registering a browser push subscription."""
    endpoint: str = Field(..., min_length=8, description="Browser push endpoint URL")
    p256dh_key: str = Field(..., min_length=1, description="Client ECDH public key (base64url)")
    auth_key: str = Field(..., min_length=1, description="Client auth secret (base64url)")
    user_agent: str | None = Field(None, max_length=500, description="User Agent for device identification")

    @field_validator("endpoint")
    @classmethod
    def validate_endpoint(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed.startswith("https://"):
            raise ValueError("Push subscription endpoint must use HTTPS.")
        return trimmed

    model_config = ConfigDict(extra="ignore")


class PushSubscriptionDelete(BaseModel):
    """Schema for unregistering/deactivating a push subscription."""
    endpoint: str = Field(..., min_length=8, description="Browser push endpoint URL to remove")

    @field_validator("endpoint")
    @classmethod
    def validate_endpoint(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed.startswith("https://"):
            raise ValueError("Push subscription endpoint must use HTTPS.")
        return trimmed

    model_config = ConfigDict(extra="ignore")


class PushSubscriptionResponse(BaseModel):
    """Safe response schema for a registered push subscription."""
    id: UUID
    user_id: UUID
    endpoint: str
    user_agent: str | None = None
    is_active: bool
    created_at: datetime
    last_used_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class VapidPublicKeyResponse(BaseModel):
    """Public VAPID key response for frontend PushManager subscription."""
    vapid_public_key: str

    model_config = ConfigDict(extra="ignore")


class PushStatusResponse(BaseModel):
    """Subscription status response for current authenticated user."""
    has_active_subscription: bool
    active_count: int

    model_config = ConfigDict(extra="ignore")


class PushUnsubscribeResponse(BaseModel):
    """Response after unregistering a push subscription."""
    status: str = "unsubscribed"

    model_config = ConfigDict(extra="ignore")
