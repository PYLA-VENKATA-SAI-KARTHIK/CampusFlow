"""
Admin schemas — DTOs for user management, bulk import, and audit log listing.

Security: AdminUserResponse NEVER exposes password_hash.
Audit log old_state/new_state MUST be stripped of secrets before persistence.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


# ---------------------------------------------------------------------------
# User Management
# ---------------------------------------------------------------------------


class AdminUserListParams(BaseModel):
    """Query params for GET /admin/users."""

    role: str | None = None
    is_active: bool | None = None
    search: str | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class AdminCreateUserRequest(BaseModel):
    """Body for POST /admin/users. Only OFFICER or ADMIN roles allowed."""

    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)
    role: str = Field(..., pattern=r"^(OFFICER|ADMIN)$")
    password: str = Field(..., min_length=8, max_length=72)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.lower()


class AdminUpdateUserRequest(BaseModel):
    """Body for PATCH /admin/users/{id}. Partial update."""

    role: str | None = Field(default=None, pattern=r"^(OFFICER|ADMIN|STUDENT)$")
    is_active: bool | None = None
    full_name: str | None = Field(default=None, min_length=1, max_length=255)


class AdminUserResponse(BaseModel):
    """User response — NEVER exposes password_hash."""

    id: UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    must_change_password: bool
    last_login_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Bulk Student Import
# ---------------------------------------------------------------------------


class BulkImportRowError(BaseModel):
    """Per-row error from bulk import."""

    row_number: int
    error: str


class BulkImportResponse(BaseModel):
    """Response for POST /admin/students/bulk-import."""

    total_rows: int
    success_count: int
    error_count: int
    errors: list[BulkImportRowError] = []


# ---------------------------------------------------------------------------
# Audit Logs
# ---------------------------------------------------------------------------


class AdminAuditLogListParams(BaseModel):
    """Query params for GET /admin/audit-logs."""

    user_id: UUID | None = None
    entity_type: str | None = None
    action: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class AdminAuditLogResponse(BaseModel):
    """Audit log entry response."""

    id: UUID
    performed_by_user_id: UUID | None = None
    action: str
    entity_type: str
    entity_id: UUID | None = None
    old_state: dict[str, Any] | None = None
    new_state: dict[str, Any] | None = None
    ip_address: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("ip_address", mode="before")
    @classmethod
    def coerce_ip_to_str(cls, v: Any) -> str | None:
        """PostgreSQL INET column returns IPv4Address/IPv6Address objects."""
        if v is None:
            return None
        return str(v)

