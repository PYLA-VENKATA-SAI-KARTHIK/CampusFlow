"""
Drive Registration Repository.
"""
from typing import Sequence
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.drive_registration import DriveRegistration
from app.models.placement_drive import PlacementDrive
from app.models.company import Company
from app.models.student_profile import StudentProfile
from app.models.user import User


class DriveRegistrationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_drive_and_student(self, drive_id: UUID, student_user_id: UUID) -> DriveRegistration | None:
        stmt = select(DriveRegistration).where(
            DriveRegistration.drive_id == drive_id,
            DriveRegistration.student_user_id == student_user_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_registered_student_ids_for_drive(self, drive_id: UUID) -> set[UUID]:
        stmt = select(DriveRegistration.student_user_id).where(
            DriveRegistration.drive_id == drive_id,
            DriveRegistration.status == "REGISTERED",
        )
        result = await self.session.execute(stmt)
        return set(result.scalars().all())


    async def create(self, registration: DriveRegistration) -> DriveRegistration:
        self.session.add(registration)
        await self.session.flush()
        return registration

    async def list_by_drive_id(self, drive_id: UUID, skip: int = 0, limit: int = 20, status: str | None = None, branch: str | None = None) -> tuple[Sequence[tuple[DriveRegistration, StudentProfile, User]], int]:
        # Count total
        count_stmt = select(func.count()).select_from(DriveRegistration).join(
            User, DriveRegistration.student_user_id == User.id
        ).join(
            StudentProfile, User.id == StudentProfile.user_id
        ).where(DriveRegistration.drive_id == drive_id)

        if status:
            count_stmt = count_stmt.where(DriveRegistration.status == status)
        if branch:
            count_stmt = count_stmt.where(func.lower(StudentProfile.branch_code) == branch.lower())
            
        total = await self.session.scalar(count_stmt) or 0

        # Fetch items
        stmt = select(DriveRegistration, StudentProfile, User).join(
            User, DriveRegistration.student_user_id == User.id
        ).join(
            StudentProfile, User.id == StudentProfile.user_id
        ).where(DriveRegistration.drive_id == drive_id)

        if status:
            stmt = stmt.where(DriveRegistration.status == status)
        if branch:
            stmt = stmt.where(func.lower(StudentProfile.branch_code) == branch.lower())

        stmt = stmt.order_by(DriveRegistration.registered_at.desc()).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return result.all(), total

    async def list_student_applications(self, student_user_id: UUID, skip: int = 0, limit: int = 20, status: str | None = None) -> tuple[Sequence[tuple[DriveRegistration, PlacementDrive, Company]], int]:
        # Count total
        count_stmt = select(func.count()).select_from(DriveRegistration).join(
            PlacementDrive, DriveRegistration.drive_id == PlacementDrive.id
        ).where(DriveRegistration.student_user_id == student_user_id)

        if status:
            count_stmt = count_stmt.where(DriveRegistration.status == status)

        total = await self.session.scalar(count_stmt) or 0

        # Fetch items
        stmt = select(DriveRegistration, PlacementDrive, Company).join(
            PlacementDrive, DriveRegistration.drive_id == PlacementDrive.id
        ).join(
            Company, PlacementDrive.company_id == Company.id
        ).where(DriveRegistration.student_user_id == student_user_id)

        if status:
            stmt = stmt.where(DriveRegistration.status == status)

        stmt = stmt.order_by(DriveRegistration.registered_at.desc()).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return result.all(), total
