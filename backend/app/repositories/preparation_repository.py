"""
Preparation Hub repository.
"""
from typing import Sequence
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.preparation import (
    PreparationCategory,
    PreparationMaterial,
    PreparationRole,
    PreparationRoleTopic,
    PreparationTopic,
)


class PreparationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_roles(self, only_active: bool = True) -> Sequence[PreparationRole]:
        stmt = select(PreparationRole).order_by(PreparationRole.name)
        if only_active:
            stmt = stmt.where(PreparationRole.is_active.is_(True))
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_role_by_code(self, code: str) -> PreparationRole | None:
        stmt = (
            select(PreparationRole)
            .where(PreparationRole.code == code)
            .options(
                selectinload(PreparationRole.role_topics).selectinload(PreparationRoleTopic.topic)
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_categories_with_topics(self) -> Sequence[PreparationCategory]:
        stmt = (
            select(PreparationCategory)
            .order_by(PreparationCategory.sequence_order, PreparationCategory.name)
            .options(selectinload(PreparationCategory.topics))
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def list_materials(
        self,
        category_id: UUID | None = None,
        topic_id: UUID | None = None,
        role_id: UUID | None = None,
        difficulty: str | None = None,
        material_type: str | None = None,
        search: str | None = None,
        status: str = "APPROVED",
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[Sequence[PreparationMaterial], int]:
        stmt = (
            select(PreparationMaterial)
            .where(PreparationMaterial.status == status)
            .options(
                selectinload(PreparationMaterial.topic),
                selectinload(PreparationMaterial.role),
            )
        )

        if topic_id:
            stmt = stmt.where(PreparationMaterial.topic_id == topic_id)
        elif category_id:
            stmt = stmt.join(PreparationMaterial.topic).where(
                PreparationTopic.category_id == category_id
            )

        if role_id:
            stmt = stmt.where(PreparationMaterial.role_id == role_id)

        if difficulty:
            stmt = stmt.where(PreparationMaterial.difficulty == difficulty)

        if material_type:
            stmt = stmt.where(PreparationMaterial.material_type == material_type)

        if search:
            stmt = stmt.where(
                PreparationMaterial.title.ilike(f"%{search}%")
                | PreparationMaterial.description.ilike(f"%{search}%")
            )

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.session.execute(count_stmt)).scalar() or 0

        # Pagination and order
        stmt = (
            stmt.order_by(PreparationMaterial.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await self.session.execute(stmt)
        return result.scalars().all(), total

    async def get_material_by_id(self, material_id: UUID) -> PreparationMaterial | None:
        stmt = (
            select(PreparationMaterial)
            .where(PreparationMaterial.id == material_id)
            .options(
                selectinload(PreparationMaterial.topic),
                selectinload(PreparationMaterial.role),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_material(self, material: PreparationMaterial) -> PreparationMaterial:
        self.session.add(material)
        await self.session.flush()
        await self.session.refresh(material)
        return material

    async def list_pending_submissions(
        self, page: int = 1, page_size: int = 20
    ) -> tuple[Sequence[PreparationMaterial], int]:
        return await self.list_materials(status="PENDING", page=page, page_size=page_size)

    async def list_student_submissions(
        self, user_id: UUID, page: int = 1, page_size: int = 20
    ) -> tuple[Sequence[PreparationMaterial], int]:
        stmt = (
            select(PreparationMaterial)
            .where(PreparationMaterial.submitted_by_user_id == user_id)
            .options(
                selectinload(PreparationMaterial.topic),
                selectinload(PreparationMaterial.role),
            )
        )
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.session.execute(count_stmt)).scalar() or 0

        stmt = (
            stmt.order_by(PreparationMaterial.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all(), total

    async def count_materials_for_topic(self, topic_id: UUID) -> int:
        stmt = (
            select(func.count(PreparationMaterial.id))
            .where(
                PreparationMaterial.topic_id == topic_id,
                PreparationMaterial.status == "APPROVED",
            )
        )
        return (await self.session.execute(stmt)).scalar() or 0
