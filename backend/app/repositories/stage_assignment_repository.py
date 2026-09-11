"""
Stage Assignment repository.
"""
from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.placement_stage import PlacementStage
from app.models.stage_assignment import StageAssignment


class StageAssignmentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_student_assignments_for_drives(
        self, student_user_id: UUID, drive_ids: list[UUID]
    ) -> Sequence[StageAssignment]:
        """
        Get the latest published stage assignment for a student across multiple drives.
        Uses DISTINCT ON (drive_id) ordered by sequence_order DESC.
        """
        if not drive_ids:
            return []

        stmt = (
            select(StageAssignment)
            .join(PlacementStage)
            .options(joinedload(StageAssignment.stage))
            .where(
                StageAssignment.student_user_id == student_user_id,
                StageAssignment.drive_id.in_(drive_ids),
                PlacementStage.is_published == True,
            )
            .distinct(StageAssignment.drive_id)
            .order_by(StageAssignment.drive_id, PlacementStage.sequence_order.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_assignment(self, stage_id: UUID, student_user_id: UUID) -> StageAssignment | None:
        stmt = select(StageAssignment).where(
            StageAssignment.stage_id == stage_id,
            StageAssignment.student_user_id == student_user_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_assignments_for_stage(self, stage_id: UUID) -> Sequence[StageAssignment]:
        stmt = select(StageAssignment).where(StageAssignment.stage_id == stage_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def upsert_assignments(self, stage_id: UUID, drive_id: UUID, student_ids: list[UUID], status: str = "SHORTLISTED") -> None:
        if not student_ids:
            return
            
        from sqlalchemy.dialects.postgresql import insert
        
        values = [
            {
                "stage_id": stage_id,
                "student_user_id": student_id,
                "drive_id": drive_id,
                "status": status,
            }
            for student_id in student_ids
        ]
        
        stmt = insert(StageAssignment).values(values)
        stmt = stmt.on_conflict_do_update(
            index_elements=["stage_id", "student_user_id"],
            set_={"status": stmt.excluded.status}
        )
        await self.session.execute(stmt)

    async def update_assignment(self, assignment: StageAssignment, data: dict) -> StageAssignment:
        for key, value in data.items():
            if value is not None or key in ["result_notes"]:
                setattr(assignment, key, value)
        self.session.add(assignment)
        await self.session.flush()
        await self.session.refresh(assignment)
        return assignment
