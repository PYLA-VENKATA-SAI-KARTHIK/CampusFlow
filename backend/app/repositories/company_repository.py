"""
Company repository.
"""
from __future__ import annotations

from typing import Sequence
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company


class CompanyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, company_id: UUID) -> Company | None:
        return await self.session.get(Company, company_id)

    async def list_companies(self, skip: int = 0, limit: int = 20) -> tuple[Sequence[Company], int]:
        count_stmt = select(func.count(Company.id))
        total = await self.session.scalar(count_stmt) or 0

        stmt = select(Company).order_by(Company.name).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all(), total

    def add(self, company: Company) -> None:
        self.session.add(company)
