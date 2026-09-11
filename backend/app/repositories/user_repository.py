"""
User repository.
"""
from __future__ import annotations

from typing import Sequence
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.student_profile import StudentProfile
from app.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, user_id: UUID | str) -> User | None:
        if isinstance(user_id, str):
            try:
                user_id = UUID(user_id)
            except ValueError:
                return None
        return await self.session.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email.lower())
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def add(self, user: User) -> None:
        self.session.add(user)

    # -------------------------------------------------------------------------
    # Admin — User listing (paginated, filtered, searchable)
    # -------------------------------------------------------------------------

    async def list_users(
        self,
        skip: int = 0,
        limit: int = 20,
        role: str | None = None,
        is_active: bool | None = None,
        search: str | None = None,
    ) -> tuple[Sequence[User], int]:
        """
        List users with optional filters and search.
        Returns (users, total_count).
        """
        base_stmt = select(User)

        if role is not None:
            base_stmt = base_stmt.where(User.role == role)
        if is_active is not None:
            base_stmt = base_stmt.where(User.is_active == is_active)  # noqa: E712
        if search:
            search_term = f"%{search}%"
            base_stmt = base_stmt.where(
                (User.full_name.ilike(search_term)) | (User.email.ilike(search_term))
            )

        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total = await self.session.scalar(count_stmt) or 0

        stmt = (
            base_stmt
            .order_by(User.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all(), total

    # -------------------------------------------------------------------------
    # Admin — Last-admin protection
    # -------------------------------------------------------------------------

    async def count_active_admins(self) -> int:
        """Count active users with ADMIN role."""
        stmt = select(func.count()).where(
            User.role == "ADMIN",
            User.is_active == True,  # noqa: E712
        )
        return await self.session.scalar(stmt) or 0
