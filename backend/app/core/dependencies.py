"""
CampusFlow — FastAPI Dependencies

Provides reusable dependency-injected components:
- get_current_user: verify Bearer JWT, return UserContext
- require_role: enforce RBAC (never trusts frontend)
- get_db: async SQLAlchemy session

Authorization always happens server-side. Frontend role-hiding is cosmetic only.
"""
from __future__ import annotations

import logging
from typing import Annotated

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AccountNotActiveError,
    AuthenticationError,
    InvalidTokenError,
    MustChangePasswordError,
    PermissionDeniedError,
)
from app.core.security import get_jwt_manager
from app.db.session import get_db_session

logger = logging.getLogger(__name__)

_bearer_scheme = HTTPBearer(auto_error=False)


# ---------------------------------------------------------------------------
# User context — populated from JWT claims
# ---------------------------------------------------------------------------


class UserContext:
    """Lightweight user context extracted from a verified JWT. No DB lookup."""

    __slots__ = ("user_id", "role", "email")

    def __init__(self, user_id: str, role: str, email: str) -> None:
        self.user_id = user_id
        self.role = role
        self.email = email

    def __repr__(self) -> str:
        return f"UserContext(user_id={self.user_id!r}, role={self.role!r})"


# ---------------------------------------------------------------------------
# Authentication dependency
# ---------------------------------------------------------------------------


async def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Security(_bearer_scheme)
    ] = None,
) -> UserContext:
    """
    Verify Bearer JWT. Returns UserContext on success.
    Raises HTTP 401 on any failure — same error regardless of failure type
    to avoid leaking information about token structure.

    NEVER logs the raw token.
    """
    if credentials is None:
        raise AuthenticationError("Authentication credentials were not provided.")

    raw_token = credentials.credentials  # noqa: S105 — never logged

    try:
        jwt_mgr = get_jwt_manager()
        payload = jwt_mgr.decode_access_token(raw_token)
    except JWTError:
        # Do not reveal the specific JWT error to the caller
        raise InvalidTokenError("Token is invalid or has expired.")

    user_id = payload.get("sub")
    role = payload.get("role")
    email = payload.get("email")

    if not user_id or not role or not email:
        raise InvalidTokenError("Token payload is malformed.")

    return UserContext(user_id=user_id, role=role, email=email)


# ---------------------------------------------------------------------------
# RBAC dependency factory
# ---------------------------------------------------------------------------


def require_role(*allowed_roles: str):
    """
    Returns a FastAPI dependency that checks the authenticated user's role.

    Usage:
        @router.get("/officer-only", dependencies=[Depends(require_role("OFFICER", "ADMIN"))])

    Security guarantee: role comes from verified JWT — never from request body.
    """

    async def _check_role(
        current_user: Annotated[UserContext, Depends(get_current_user)],
    ) -> UserContext:
        if current_user.role not in allowed_roles:
            logger.warning(
                "Permission denied: user %s (role=%s) attempted restricted action (allowed=%s)",
                current_user.user_id,
                current_user.role,
                allowed_roles,
            )
            raise PermissionDeniedError(
                "You do not have permission to perform this action."
            )
        return current_user

    return _check_role


# ---------------------------------------------------------------------------
# Database session dependency
# ---------------------------------------------------------------------------


async def get_db() -> AsyncSession:  # type: ignore[misc]
    """Yield an async database session for a single request."""
    async for session in get_db_session():
        yield session
