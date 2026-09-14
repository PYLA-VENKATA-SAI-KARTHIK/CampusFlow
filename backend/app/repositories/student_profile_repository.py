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

    async def get_by_roll_number(self, roll_number: str) -> StudentProfile | None:
        """Find a student profile by roll number / registration number (case-insensitive, trimmed)."""
        clean = roll_number.strip().lower()
        stmt = (
            select(StudentProfile)
            .options(
                selectinload(StudentProfile.user),
                selectinload(StudentProfile.branch),
            )
            .where(func.lower(StudentProfile.roll_number) == clean)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


    async def list_students(
        self, 
        skip: int = 0, 
        limit: int = 20, 
        branch_code: str | None = None,
        batch_year: int | None = None,
        min_cgpa: float | None = None,
        search: str | None = None
    ) -> tuple[Sequence[StudentProfile], int]:
        
        base_stmt = select(StudentProfile).join(User, StudentProfile.user_id == User.id)

        if branch_code:
            base_stmt = base_stmt.where(StudentProfile.branch_code == branch_code)
        if batch_year:
            base_stmt = base_stmt.where(StudentProfile.batch_year == batch_year)
        if min_cgpa is not None:
            base_stmt = base_stmt.where(StudentProfile.cgpa >= min_cgpa)
        if search:
            search_term = f"%{search}%"
            base_stmt = base_stmt.where(
                (StudentProfile.roll_number.ilike(search_term)) |
                (User.full_name.ilike(search_term)) |
                (User.email.ilike(search_term))
            )

        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total = await self.session.scalar(count_stmt) or 0

        stmt = (
            base_stmt
            .options(
                selectinload(StudentProfile.user),
                selectinload(StudentProfile.branch)
            )
            .order_by(StudentProfile.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        
        result = await self.session.execute(stmt)
        return result.scalars().all(), total

    async def list_all_active_profiles(self) -> Sequence[StudentProfile]:
        """Fetch all student profiles belonging to active users."""
        stmt = (
            select(StudentProfile)
            .join(User, StudentProfile.user_id == User.id)
            .where(User.is_active == True)  # noqa: E712
            .options(
                selectinload(StudentProfile.user),
                selectinload(StudentProfile.branch),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    def add(self, profile: StudentProfile) -> None:
        self.session.add(profile)

