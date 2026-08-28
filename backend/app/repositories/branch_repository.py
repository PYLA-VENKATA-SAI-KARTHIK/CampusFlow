"""
Branch repository.
"""
from __future__ import annotations

from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.branch import Branch


class BranchRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_all(self, include_inactive: bool = False) -> Sequence[Branch]:
        stmt = select(Branch).order_by(Branch.code)
        if not include_inactive:
            stmt = stmt.where(Branch.is_active.is_(True))
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_code(self, code: str) -> Branch | None:
        stmt = select(Branch).where(Branch.code == code.upper())
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def add(self, branch: Branch) -> None:
        self.session.add(branch)
