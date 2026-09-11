"""
Placement Stage repository.
"""
from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.placement_stage import PlacementStage
from app.schemas.placement_stage import PlacementStageUpdate


class PlacementStageRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, stage: PlacementStage) -> PlacementStage:
        self.session.add(stage)
        await self.session.flush()
        await self.session.refresh(stage)
        return stage

    async def get_by_id(self, stage_id: UUID) -> PlacementStage | None:
        stmt = select(PlacementStage).where(PlacementStage.id == stage_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_drive_id(self, drive_id: UUID) -> Sequence[PlacementStage]:
        stmt = select(PlacementStage).where(PlacementStage.drive_id == drive_id).order_by(PlacementStage.sequence_order)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update(self, stage: PlacementStage, update_data: PlacementStageUpdate) -> PlacementStage:
        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(stage, key, value)
        await self.session.flush()
        await self.session.refresh(stage)
        return stage

    async def publish(self, stage: PlacementStage) -> PlacementStage:
        stage.is_published = True
        await self.session.flush()
        await self.session.refresh(stage)
        return stage
