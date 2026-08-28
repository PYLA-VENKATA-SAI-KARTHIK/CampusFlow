"""
Auth-related data access (Refresh tokens, Account activations).
"""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account_activation import AccountActivation
from app.models.refresh_token import RefreshToken


class AuthRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # -------------------------------------------------------------------------
    # Refresh Tokens
    # -------------------------------------------------------------------------

    async def get_refresh_token(self, token_hash: str) -> RefreshToken | None:
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def add_refresh_token(self, token: RefreshToken) -> None:
        self.session.add(token)

    async def revoke_all_for_user(self, user_id: UUID | str) -> None:
        if isinstance(user_id, str):
            user_id = UUID(user_id)
        # Using a raw delete query for efficiency instead of loading models
        stmt = delete(RefreshToken).where(RefreshToken.user_id == user_id)
        await self.session.execute(stmt)

    async def cleanup_expired_tokens(self) -> None:
        now = datetime.now(timezone.utc)
        stmt = delete(RefreshToken).where(RefreshToken.expires_at < now)
        await self.session.execute(stmt)

    # -------------------------------------------------------------------------
    # Account Activations
    # -------------------------------------------------------------------------

    async def get_activation_by_hash(self, token_hash: str) -> AccountActivation | None:
        stmt = select(AccountActivation).where(AccountActivation.token_hash == token_hash)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_activation_by_user(self, user_id: UUID | str) -> AccountActivation | None:
        if isinstance(user_id, str):
            user_id = UUID(user_id)
        stmt = select(AccountActivation).where(AccountActivation.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def add_activation(self, activation: AccountActivation) -> None:
        self.session.add(activation)
