"""
Authentication service logic.
Handles login, refresh, logout, and account activation.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.email import ActivationEmailData, EmailService
from app.core.exceptions import (
    AccountAlreadyRegisteredError,
    AccountNotActiveError,
    AccountNotEligibleForRegistrationError,
    ActivationTokenExpiredError,
    ActivationTokenInvalidError,
    ActivationTokenUsedError,
    AuthenticationError,
    InvalidTokenError,
    MustChangePasswordError,
    ResendRateLimitError,
    StudentNotFoundError,
)
from app.core.security import (
    generate_secure_token,
    get_jwt_manager,
    hash_password,
    hash_token,
    verify_password,
)
from app.models.account_activation import AccountActivation
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.repositories.auth_repository import AuthRepository
from app.repositories.student_profile_repository import StudentProfileRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import RegisterResponse, TokenResponse
from app.schemas.user import UserResponse

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, session: AsyncSession, email_service: EmailService) -> None:
        self.session = session
        self.email_service = email_service
        self.user_repo = UserRepository(session)
        self.auth_repo = AuthRepository(session)
        self.settings = get_settings()

    async def authenticate(self, email: str, password: str) -> TokenResponse:
        """
        Authenticate user and return access + refresh tokens.
        Accepts either email address or student registration number.
        Raises AuthenticationError if invalid credentials.
        Raises AccountNotActiveError if user is not active.
        """
        clean_identifier = email.strip()
        user = await self.user_repo.get_by_email(clean_identifier)
        if not user:
            student_repo = StudentProfileRepository(self.session)
            profile = await student_repo.get_by_roll_number(clean_identifier)
            if profile and profile.user:
                user = profile.user

        if not user:
            # We delay slightly to prevent timing attacks, though bcrypt is already slow
            hash_password("dummy")
            raise AuthenticationError("Invalid email or password.")


        if not verify_password(password, user.password_hash):
            raise AuthenticationError("Invalid email or password.")

        if not user.is_active:
            raise AccountNotActiveError()

        # Update last login
        user.last_login_at = datetime.now(timezone.utc)
        self.session.add(user)

        # Issue tokens
        jwt_mgr = get_jwt_manager()
        access_token = jwt_mgr.create_access_token(str(user.id), user.role, user.email)
        
        raw_refresh_token = generate_secure_token()
        refresh_token_hash = hash_token(raw_refresh_token)
        
        expires_at = datetime.now(timezone.utc) + timedelta(
            seconds=self.settings.jwt_refresh_token_expire_seconds
        )

        db_token = RefreshToken(
            user_id=user.id,
            token_hash=refresh_token_hash,
            expires_at=expires_at,
        )
        self.auth_repo.add_refresh_token(db_token)
        
        await self.session.commit()

        return TokenResponse(
            access_token=access_token,
            refresh_token=raw_refresh_token,
            user=UserResponse.model_validate(user),
        )

    async def refresh_tokens(self, raw_refresh_token: str) -> TokenResponse:
        """
        Exchange a valid refresh token for a new access token.
        Always rotates the refresh token.
        """
        token_hash = hash_token(raw_refresh_token)
        db_token = await self.auth_repo.get_refresh_token(token_hash)

        if not db_token:
            raise InvalidTokenError("Invalid refresh token.")

        if db_token.revoked:
            # If a revoked token is used, we should ideally revoke all tokens for this user
            # as it might indicate token theft.
            await self.auth_repo.revoke_all_for_user(db_token.user_id)
            await self.session.commit()
            raise InvalidTokenError("Token has been revoked.")

        now = datetime.now(timezone.utc)
        if db_token.expires_at < now:
            raise InvalidTokenError("Token has expired.")

        user = await self.user_repo.get_by_id(db_token.user_id)
        if not user or not user.is_active:
            raise AccountNotActiveError()

        # Revoke the old token (rotation)
        db_token.revoked = True
        self.session.add(db_token)

        # Issue new tokens
        jwt_mgr = get_jwt_manager()
        access_token = jwt_mgr.create_access_token(str(user.id), user.role, user.email)
        
        new_raw_refresh_token = generate_secure_token()
        new_refresh_token_hash = hash_token(new_raw_refresh_token)
        
        expires_at = now + timedelta(
            seconds=self.settings.jwt_refresh_token_expire_seconds
        )

        new_db_token = RefreshToken(
            user_id=user.id,
            token_hash=new_refresh_token_hash,
            expires_at=expires_at,
        )
        self.auth_repo.add_refresh_token(new_db_token)
        
        await self.session.commit()

        return TokenResponse(
            access_token=access_token,
            refresh_token=new_raw_refresh_token,
            user=UserResponse.model_validate(user),
        )

    async def logout(self, raw_refresh_token: str) -> None:
        """Revoke a single refresh token."""
        token_hash = hash_token(raw_refresh_token)
        db_token = await self.auth_repo.get_refresh_token(token_hash)
        if db_token and not db_token.revoked:
            db_token.revoked = True
            self.session.add(db_token)
            await self.session.commit()

    async def activate_account(self, raw_token: str, new_password: str) -> None:
        """
        Complete account activation using a valid token.
        Sets password, marks user active, clears must_change_password.
        """
        token_hash = hash_token(raw_token)
        activation = await self.auth_repo.get_activation_by_hash(token_hash)

        if not activation:
            raise ActivationTokenInvalidError()

        if activation.used:
            raise ActivationTokenUsedError()

        if activation.expires_at < datetime.now(timezone.utc):
            raise ActivationTokenExpiredError()

        user = await self.user_repo.get_by_id(activation.user_id)
        if not user:
            raise ActivationTokenInvalidError()

        # Apply changes
        user.password_hash = hash_password(new_password)
        user.is_active = True
        user.must_change_password = False
        activation.used = True

        self.session.add(user)
        self.session.add(activation)
        
        # Future: Write audit log here
        
        await self.session.commit()

    async def register_student(
        self, registration_number: str, password: str
    ) -> RegisterResponse:
        """
        Complete first-time student registration using student registration number.
        - Verifies pre-provisioned student profile exists.
        - Resolves associated user account.
        - Verifies eligibility for first-time registration (not already active, role == STUDENT).
        - Hashes password with bcrypt.
        - Marks user active and clears must_change_password.
        - Marks any existing AccountActivation record as used.
        - Preserves all academic fields on StudentProfile.
        - Returns confirmation response with registered email.
        """
        student_repo = StudentProfileRepository(self.session)
        clean_reg_no = registration_number.strip()
        profile = await student_repo.get_by_roll_number(clean_reg_no)

        if not profile:
            raise StudentNotFoundError(
                "Registration number not found. Please contact your placement office."
            )

        user = profile.user
        if not user:
            raise StudentNotFoundError(
                "Registration number not found. Please contact your placement office."
            )

        # Check if already activated / registered
        if user.is_active:
            raise AccountAlreadyRegisteredError(
                "This student account is already registered. Please sign in."
            )

        # Check role eligibility
        if user.role != "STUDENT":
            raise AccountNotEligibleForRegistrationError(
                "This student account is not eligible for registration."
            )

        # Hash the password securely and assign university email
        university_email = f"{clean_reg_no}@klu.ac.in"
        user.email = university_email
        user.password_hash = hash_password(password)
        user.is_active = True
        user.must_change_password = False
        user.last_login_at = datetime.now(timezone.utc)
        self.session.add(user)

        # If an activation token was provisioned (e.g. from bulk import), mark it used
        activation = await self.auth_repo.get_activation_by_user(user.id)
        if activation:
            activation.used = True
            self.session.add(activation)

        await self.session.commit()

        return RegisterResponse(
            message="Registration completed successfully. You can now sign in.",
            email=user.email,
            registration_number=profile.roll_number,
        )

