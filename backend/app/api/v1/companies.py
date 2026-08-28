"""
Company management endpoints.
"""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import UserContext, get_current_user, get_db, require_role
from app.repositories.company_repository import CompanyRepository
from app.schemas.common import PaginatedResponse
from app.schemas.company import CompanyCreate, CompanyResponse
from app.services.company_service import CompanyService

router = APIRouter()


def get_company_service(session: AsyncSession = Depends(get_db)) -> CompanyService:
    repo = CompanyRepository(session)
    return CompanyService(repo)


@router.post("", response_model=CompanyResponse, status_code=201)
async def create_company(
    data: CompanyCreate,
    current_user: Annotated[UserContext, Depends(require_role("OFFICER", "ADMIN"))],
    service: Annotated[CompanyService, Depends(get_company_service)],
) -> CompanyResponse:
    """Create a new company. Restricted to OFFICER and ADMIN."""
    return await service.create_company(data, current_user.user_id)


@router.get("", response_model=PaginatedResponse[CompanyResponse])
async def list_companies(
    current_user: Annotated[UserContext, Depends(get_current_user)],
    service: Annotated[CompanyService, Depends(get_company_service)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[CompanyResponse]:
    """List all companies. Accessible to all authenticated users."""
    skip = (page - 1) * page_size
    companies, total = await service.list_companies(skip=skip, limit=page_size)
    
    return PaginatedResponse(
        items=list(companies),
        total=total,
        page=page,
        page_size=page_size,
        has_next=(skip + page_size) < total
    )


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: UUID,
    current_user: Annotated[UserContext, Depends(get_current_user)],
    service: Annotated[CompanyService, Depends(get_company_service)],
) -> CompanyResponse:
    """Get a specific company. Accessible to all authenticated users."""
    return await service.get_company(company_id)
