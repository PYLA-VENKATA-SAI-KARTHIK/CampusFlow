"""
Push Subscription repository.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Sequence
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, PermissionDeniedError
from app.models.push_subscription import PushSubscription


class PushSubscriptionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_endpoint(self, endpoint: str) -> PushSubscription | None:
        """Find a subscription by its unique endpoint URL."""
        stmt = select(PushSubscription).where(PushSubscription.endpoint == endpoint)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_subscriptions_for_user(self, user_id: UUID | str) -> Sequence[PushSubscription]:
        """Fetch all active subscriptions belonging to a user."""
        uid = UUID(str(user_id)) if not isinstance(user_id, UUID) else user_id
        stmt = (
            select(PushSubscription)
            .where(
                PushSubscription.user_id == uid,
                PushSubscription.is_active == True,  # noqa: E712
            )
            .order_by(PushSubscription.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count_active_for_user(self, user_id: UUID | str) -> int:
        """Count active subscriptions for a user."""
        uid = UUID(str(user_id)) if not isinstance(user_id, UUID) else user_id
        stmt = (
            select(func.count(PushSubscription.id))
            .where(
                PushSubscription.user_id == uid,
                PushSubscription.is_active == True,  # noqa: E712
            )
        )
        return await self.session.scalar(stmt) or 0

    async def upsert_subscription(
        self,
        user_id: UUID | str,
        endpoint: str,
        p256dh_key: str,
        auth_key: str,
        user_agent: str | None = None,
    ) -> PushSubscription:
        """
        Register or reactivate a browser push subscription for the given user.
        Security Guarantee:
        - If the endpoint already belongs to this user, updates keys and reactivates it.
        - If the endpoint belongs to another user, strictly rejects the request to prevent hijacking.
        - If the endpoint is new, creates a new subscription row.
        """
        uid = UUID(str(user_id)) if not isinstance(user_id, UUID) else user_id
        existing = await self.get_by_endpoint(endpoint)

        if existing:
            if str(existing.user_id) != str(uid):
                raise ConflictError("Push subscription endpoint already registered to another user account.")

            # Update existing subscription for same user
            existing.p256dh_key = p256dh_key
            existing.auth_key = auth_key
            existing.user_agent = user_agent
            existing.is_active = True
            self.session.add(existing)
            await self.session.flush()
            await self.session.refresh(existing)
            return existing

        new_sub = PushSubscription(
            user_id=uid,
            endpoint=endpoint,
            p256dh_key=p256dh_key,
            auth_key=auth_key,
            user_agent=user_agent,
            is_active=True,
        )
        self.session.add(new_sub)
        await self.session.flush()
        await self.session.refresh(new_sub)
        return new_sub

    async def deactivate_by_endpoint(self, user_id: UUID | str, endpoint: str) -> bool:
        """
        Deactivate a subscription by endpoint strictly for the authenticated user (IDOR-safe).
        Returns True if deactivated, False if not found or not owned by user.
        """
        uid = UUID(str(user_id)) if not isinstance(user_id, UUID) else user_id
        existing = await self.get_by_endpoint(endpoint)
        if not existing or str(existing.user_id) != str(uid):
            return False

        existing.is_active = False
        self.session.add(existing)
        await self.session.flush()
        return True

    async def mark_subscription_used(
        self, subscription_id: UUID, now: datetime | None = None
    ) -> None:
        """Update last_used_at on successful push delivery."""
        if now is None:
            now = datetime.now(timezone.utc)
        stmt = (
            update(PushSubscription)
            .where(PushSubscription.id == subscription_id)
            .values(last_used_at=now)
        )
        await self.session.execute(stmt)

    async def mark_subscription_inactive(self, subscription_id: UUID) -> None:
        """Deactivate an expired / invalid subscription (HTTP 410 Gone / 404)."""
        stmt = (
            update(PushSubscription)
            .where(PushSubscription.id == subscription_id)
            .values(is_active=False)
        )
        await self.session.execute(stmt)
