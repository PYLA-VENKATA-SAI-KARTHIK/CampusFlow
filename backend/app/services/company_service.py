"""
Company service.
"""
from __future__ import annotations

from typing import Sequence
from uuid import UUID

from fastapi import HTTPException, status

from app.models.company import Company
from app.repositories.company_repository import CompanyRepository
from app.schemas.company import CompanyCreate


class CompanyService:
    def __init__(self, company_repo: CompanyRepository) -> None:
        self.company_repo = company_repo

    async def create_company(self, data: CompanyCreate, user_id: UUID | str) -> Company:
        if isinstance(user_id, str):
            user_id = UUID(user_id)

        company = Company(
            name=data.name,
            website=data.website,
            logo_gcs_path=data.logo_gcs_path,
            industry=data.industry,
            description=data.description,
            created_by_user_id=user_id,
        )
        self.company_repo.add(company)
        await self.company_repo.session.commit()
        await self.company_repo.session.refresh(company)
        return company

    async def get_company(self, company_id: UUID) -> Company:
        company = await self.company_repo.get_by_id(company_id)
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Company with id '{company_id}' not found."
            )
        return company

    async def list_companies(self, skip: int = 0, limit: int = 20) -> tuple[Sequence[Company], int]:
        return await self.company_repo.list_companies(skip=skip, limit=limit)
