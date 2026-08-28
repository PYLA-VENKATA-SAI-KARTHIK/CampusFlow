"""
Student Profile repository.
"""
from __future__ import annotations

from typing import Sequence
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.student_profile import StudentProfile
from app.models.user import User


class StudentProfileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_user_id(self, user_id: UUID) -> StudentProfile | None:
        stmt = (
            select(StudentProfile)
            .options(
                selectinload(StudentProfile.user),
                selectinload(StudentProfile.branch)
            )
            .where(StudentProfile.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, profile_id: UUID) -> StudentProfile | None:
        stmt = (
            select(StudentProfile)
            .options(
                selectinload(StudentProfile.user),
                selectinload(StudentProfile.branch)
            )
            .where(StudentProfile.id == profile_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_students(
        self, skip: int = 0, limit: int = 20, branch_code: str | None = None
    ) -> tuple[Sequence[StudentProfile], int]:
        count_stmt = select(func.count(StudentProfile.id))
        if branch_code:
            count_stmt = count_stmt.where(StudentProfile.branch_code == branch_code)

        total = await self.session.scalar(count_stmt) or 0

        stmt = (
            select(StudentProfile)
            .options(
                selectinload(StudentProfile.user),
                selectinload(StudentProfile.branch)
            )
            .order_by(StudentProfile.created_at.desc())
        )
        
        if branch_code:
            stmt = stmt.where(StudentProfile.branch_code == branch_code)

        stmt = stmt.offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all(), total

    def add(self, profile: StudentProfile) -> None:
        self.session.add(profile)
