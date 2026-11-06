"""
CampusFlow — Mock Interview Repository.
"""
from __future__ import annotations

from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.mock_interview import MockInterviewEvaluation, MockInterviewSession


class MockInterviewRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_session(self, session_obj: MockInterviewSession) -> MockInterviewSession:
        self.session.add(session_obj)
        await self.session.commit()
        ret = await self.get_session_by_id(session_obj.id)
        return ret or session_obj

    async def get_session_by_id(
        self, session_id: UUID, user_id: UUID | None = None
    ) -> MockInterviewSession | None:
        stmt = (
            select(MockInterviewSession)
            .options(selectinload(MockInterviewSession.evaluations))
            .where(MockInterviewSession.id == session_id)
        )
        if user_id is not None:
            stmt = stmt.where(MockInterviewSession.user_id == user_id)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_sessions_for_user(
        self, user_id: UUID
    ) -> Sequence[MockInterviewSession]:
        stmt = (
            select(MockInterviewSession)
            .options(selectinload(MockInterviewSession.evaluations))
            .where(MockInterviewSession.user_id == user_id)
            .order_by(MockInterviewSession.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def add_evaluation(
        self, evaluation: MockInterviewEvaluation
    ) -> MockInterviewEvaluation:
        self.session.add(evaluation)
        await self.session.commit()
        await self.session.refresh(evaluation)
        return evaluation

    async def save_session(
        self, session_obj: MockInterviewSession
    ) -> MockInterviewSession:
        self.session.add(session_obj)
        await self.session.commit()
        ret = await self.get_session_by_id(session_obj.id)
        return ret or session_obj
