from datetime import datetime, timezone
from typing import Sequence
from uuid import UUID


from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from app.models.notification import Notification


class NotificationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def bulk_insert_notifications(self, notifications: list[dict]) -> None:
        """
        Inserts notifications in bulk, ignoring duplicates based on the 
        (user_id, notification_type, reference_id) unique constraint.
        """
        if not notifications:
            return
            
        stmt = insert(Notification).values(notifications)
        stmt = stmt.on_conflict_do_nothing(
            index_elements=["user_id", "notification_type", "reference_id"]
        )
        await self.session.execute(stmt)

    async def list_for_user(
        self,
        user_id: UUID,
        is_read: bool | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[Sequence[Notification], int]:
        """List notifications belonging to a user, optionally filtered by read status."""
        base = select(Notification).where(Notification.user_id == user_id)
        count_stmt = select(func.count()).select_from(Notification).where(Notification.user_id == user_id)

        if is_read is not None:
            base = base.where(Notification.is_read == is_read)
            count_stmt = count_stmt.where(Notification.is_read == is_read)

        total = await self.session.scalar(count_stmt) or 0
        stmt = base.order_by(Notification.created_at.desc()).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all(), total

    async def get_by_id(self, notification_id: UUID) -> Notification | None:
        stmt = select(Notification).where(Notification.id == notification_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def mark_read(self, notification: Notification) -> Notification:
        """Mark a single notification as read (idempotent)."""
        if not notification.is_read:
            notification.is_read = True
            self.session.add(notification)
            await self.session.flush()
            await self.session.refresh(notification)
        return notification

    async def get_by_dedup(
        self,
        user_id: UUID,
        notification_type: str,
        reference_id: UUID | None,
    ) -> Notification | None:
        """Find an existing notification by its deduplication key (user_id, notification_type, reference_id)."""
        stmt = select(Notification).where(
            Notification.user_id == user_id,
            Notification.notification_type == notification_type,
        )
        if reference_id is not None:
            stmt = stmt.where(Notification.reference_id == reference_id)
        else:
            stmt = stmt.where(Notification.reference_id.is_(None))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_notified_user_ids(
        self,
        notification_type: str,
        reference_id: UUID,
    ) -> set[UUID]:
        """Fetch all user IDs who have already received a notification of this type for the given reference ID."""
        stmt = select(Notification.user_id).where(
            Notification.notification_type == notification_type,
            Notification.reference_id == reference_id,
        )
        result = await self.session.execute(stmt)
        return set(result.scalars().all())


    async def create_notification(self, notification: Notification) -> Notification:
        """Add a single notification to the session and flush."""
        self.session.add(notification)
        await self.session.flush()
        await self.session.refresh(notification)
        return notification

    async def mark_all_read(self, user_id: UUID) -> int:
        """Mark all unread notifications for a user as read. Returns the count updated."""
        stmt = (
            update(Notification)
            .where(Notification.user_id == user_id, Notification.is_read == False)  # noqa: E712
            .values(is_read=True)
            .returning(Notification.id)
        )
        result = await self.session.execute(stmt)
        return len(result.fetchall())

    async def mark_push_sent(self, notification_id: UUID, now: datetime | None = None) -> None:
        """Mark a notification record as push sent with timestamp."""
        if now is None:
            from datetime import timezone
            now = datetime.now(timezone.utc)
        stmt = (
            update(Notification)
            .where(Notification.id == notification_id)
            .values(push_sent=True, push_sent_at=now)
        )
        await self.session.execute(stmt)


