"""
Placement Drive repository.
"""
from __future__ import annotations

from typing import Sequence
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.placement_drive import PlacementDrive
from app.models.eligibility_criteria import EligibilityCriteria


class PlacementDriveRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, drive_id: UUID) -> PlacementDrive | None:
        stmt = (
            select(PlacementDrive)
            .options(
                selectinload(PlacementDrive.company),
                selectinload(PlacementDrive.eligibility_criteria)
            )
            .where(PlacementDrive.id == drive_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_drives(
        self, status: str | None = None, skip: int = 0, limit: int = 20, exclude_draft: bool = False
    ) -> tuple[Sequence[PlacementDrive], int]:
        count_stmt = select(func.count(PlacementDrive.id))
        if status:
            count_stmt = count_stmt.where(PlacementDrive.status == status)
        if exclude_draft:
            count_stmt = count_stmt.where(PlacementDrive.status != "DRAFT")

        total = await self.session.scalar(count_stmt) or 0

        stmt = (
            select(PlacementDrive)
            .options(
                selectinload(PlacementDrive.company),
                selectinload(PlacementDrive.eligibility_criteria),
            )
            .order_by(PlacementDrive.created_at.desc())
        )
        
        if status:
            stmt = stmt.where(PlacementDrive.status == status)
        if exclude_draft:
            stmt = stmt.where(PlacementDrive.status != "DRAFT")

        stmt = stmt.offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all(), total

    def add(self, drive: PlacementDrive) -> None:
        self.session.add(drive)
        
    def add_criteria(self, criteria: EligibilityCriteria) -> None:
        self.session.add(criteria)

    async def count_stages(self, drive_id: UUID) -> int:
        """Return the number of placement stages that exist for the given drive."""
        from app.models.placement_stage import PlacementStage
        stmt = select(func.count(PlacementStage.id)).where(PlacementStage.drive_id == drive_id)
        return await self.session.scalar(stmt) or 0

    async def get_open_drives_with_deadline(self) -> Sequence[PlacementDrive]:
        """Fetch all placement drives in REGISTRATION_OPEN status with a non-null deadline."""
        stmt = (
            select(PlacementDrive)
            .options(
                selectinload(PlacementDrive.company),
                selectinload(PlacementDrive.eligibility_criteria),
            )
            .where(
                PlacementDrive.status == "REGISTRATION_OPEN",
                PlacementDrive.registration_deadline.is_not(None),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_expired_open_drives(self, now: datetime) -> Sequence[PlacementDrive]:
        """Fetch all placement drives in REGISTRATION_OPEN status whose deadline has passed."""
        stmt = (
            select(PlacementDrive)
            .options(
                selectinload(PlacementDrive.company),
                selectinload(PlacementDrive.eligibility_criteria),
            )
            .where(
                PlacementDrive.status == "REGISTRATION_OPEN",
                PlacementDrive.registration_deadline.is_not(None),
                PlacementDrive.registration_deadline < now,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

