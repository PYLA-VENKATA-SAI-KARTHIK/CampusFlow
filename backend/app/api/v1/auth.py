"""
Authentication endpoints.
"""
from typing import Annotated

from fastapi import APIRouter, Depends, status
from starlette.requests import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.dependencies import UserContext, get_current_user, get_db
from app.core.email import EmailService, create_email_service
from app.core.limiter import limiter
from app.schemas.auth import (
    ActivateRequest,
    LoginRequest,
    RefreshRequest,
    TokenResponse,
)
from app.services.auth_service import AuthService

router = APIRouter()


def get_email_service() -> EmailService:
    """Dependency to inject the configured EmailService."""
    settings = get_settings()
    return create_email_service(
        provider=settings.email_provider,
        sendgrid_api_key=settings.sendgrid_api_key,
        sendgrid_from_email=settings.sendgrid_from_email,
        sendgrid_from_name=settings.sendgrid_from_name,
    )


def get_auth_service(
    session: Annotated[AsyncSession, Depends(get_db)],
    email_service: Annotated[EmailService, Depends(get_email_service)],
) -> AuthService:
    return AuthService(session=session, email_service=email_service)


@router.post("/login", response_model=TokenResponse)
@limiter.limit(get_settings().rate_limit_login)
async def login(
    request: Request,
    data: LoginRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    """Authenticate and receive tokens."""
    return await auth_service.authenticate(data.email, data.password)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: RefreshRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    """Exchange a valid refresh token for new tokens."""
    return await auth_service.refresh_tokens(request.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: RefreshRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> None:
    """Revoke a specific refresh token."""
    await auth_service.logout(request.refresh_token)


@router.post("/activate", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit(get_settings().rate_limit_activate)
async def activate(
    request: Request,
    data: ActivateRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> None:
    """Activate account using an email token."""
    await auth_service.activate_account(data.activation_token, data.new_password)


@router.get("/me")
async def get_me(
    current_user: Annotated[UserContext, Depends(get_current_user)],
) -> dict[str, str]:
    """Test endpoint to verify authentication is working."""
    return {
        "user_id": current_user.user_id,
        "role": current_user.role,
        "email": current_user.email,
    }
