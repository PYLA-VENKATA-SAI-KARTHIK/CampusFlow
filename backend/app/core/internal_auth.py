"""
CampusFlow — Internal Endpoint Security & OIDC Verification

Guarantees that internal endpoints (/internal/*) can only be accessed by
authorized system services (such as Google Cloud Tasks) and NEVER by regular
frontend user JWTs (Students, Placement Officers, Admins).
"""
from __future__ import annotations

import logging
from typing import Annotated, Any

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError

from app.core.config import get_settings
from app.core.exceptions import AuthenticationError, PermissionDeniedError
from app.core.security import get_jwt_manager

logger = logging.getLogger(__name__)

_internal_bearer = HTTPBearer(auto_error=False)


async def verify_internal_task_auth(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Security(_internal_bearer)
    ] = None,
) -> dict[str, Any]:
    """
    Verify authentication for Cloud Tasks / internal endpoints.

    Security guarantees:
    - Rejects unauthenticated requests (HTTP 401).
    - Rejects standard user JWTs (STUDENT/OFFICER/ADMIN) attempting to call internal routes (HTTP 403).
    - Validates internal auth secret in development/testing/mock mode.
    - Validates Google OIDC ID token in production Cloud Tasks mode.
    """
    if credentials is None:
        raise AuthenticationError("Internal task authentication credentials required.")

    token = credentials.credentials
    settings = get_settings()

    # 1. Reject standard CampusFlow user JWTs:
    # If the token is decodable as a CampusFlow user JWT, reject it with 403.
    try:
        jwt_mgr = get_jwt_manager()
        payload = jwt_mgr.decode_access_token(token)
        if payload and payload.get("sub") and payload.get("role"):
            logger.warning(
                "Rejected user JWT (role=%s, user=%s) attempting to call internal task endpoint",
                payload.get("role"),
                payload.get("sub"),
            )
            raise PermissionDeniedError("User tokens cannot access internal task endpoints.")
    except PermissionDeniedError:
        raise
    except Exception:
        # Not a valid CampusFlow user JWT — proceed to verify as internal service token
        pass

    # 2. Mock / Dev / Testing Mode:
    # Strictly disallow mock authentication if running in production
    is_non_production = settings.app_env in ("development", "testing")
    if is_non_production and settings.notification_task_provider == "mock":
        valid_mock_tokens = {
            settings.internal_task_auth_secret,
            "campusflow-internal-tasks-secret-dev",
            "mock-tasks-oidc-token",
            "mock-internal-token",
        }
        if token in valid_mock_tokens:
            return {"client": "cloud_tasks_service_account", "mode": "mock"}

        logger.warning("Invalid internal task token provided in mock/dev mode")
        raise AuthenticationError("Invalid internal task authentication token.")

    # 3. Production Google Cloud Tasks OIDC verification:
    try:
        from google.auth.transport import requests as google_requests  # type: ignore[import-not-found]
        from google.oauth2 import id_token  # type: ignore[import-not-found]

        request = google_requests.Request()
        claims = id_token.verify_oauth2_token(
            token,
            request,
            audience=settings.internal_service_url,
        )

        # Verify token issuer is Google
        issuer = claims.get("iss")
        if issuer not in ("accounts.google.com", "https://accounts.google.com"):
            logger.error("Invalid OIDC token issuer: %s", issuer)
            raise AuthenticationError("Invalid OIDC token issuer.")

        # Verify service account email if configured
        if settings.cloud_tasks_service_account_email:
            token_email = claims.get("email")
            if token_email != settings.cloud_tasks_service_account_email:
                logger.error(
                    "OIDC token email '%s' does not match expected Cloud Tasks SA '%s'",
                    token_email,
                    settings.cloud_tasks_service_account_email,
                )
                raise PermissionDeniedError("Unauthorized Cloud Tasks service account.")

        return claims

    except PermissionDeniedError:
        raise
    except AuthenticationError:
        raise
    except Exception as e:
        logger.error("Production OIDC verification failed: %s", str(e))
        raise AuthenticationError("OIDC token verification failed.") from e

