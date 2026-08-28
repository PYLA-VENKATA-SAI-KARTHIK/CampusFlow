"""
Student Profile endpoints for officers.
"""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import UserContext, get_db, require_role
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.student_profile_repository import StudentProfileRepository
from app.schemas.common import PaginatedResponse
from app.schemas.student_profile import StudentProfileResponse
from app.services.student_profile_service import StudentProfileService

router = APIRouter()


def get_profile_service(session: AsyncSession = Depends(get_db)) -> StudentProfileService:
    profile_repo = StudentProfileRepository(session)
    audit_repo = AuditLogRepository(session)
    return StudentProfileService(profile_repo, audit_repo)


@router.get("/students", response_model=PaginatedResponse[StudentProfileResponse])
async def list_students(
    current_user: Annotated[UserContext, Depends(require_role("OFFICER", "ADMIN"))],
    service: Annotated[StudentProfileService, Depends(get_profile_service)],
    branch_code: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[StudentProfileResponse]:
    """List all student profiles. Restricted to OFFICER and ADMIN."""
    skip = (page - 1) * page_size
    students, total = await service.list_students(skip=skip, limit=page_size, branch_code=branch_code)
    
    return PaginatedResponse(
        items=list(students),
        total=total,
        page=page,
        page_size=page_size,
        has_next=(skip + page_size) < total
    )


@router.get("/students/{student_id}", response_model=StudentProfileResponse)
async def get_student(
    student_id: UUID,
    current_user: Annotated[UserContext, Depends(require_role("OFFICER", "ADMIN"))],
    service: Annotated[StudentProfileService, Depends(get_profile_service)],
) -> StudentProfileResponse:
    """Get a specific student profile. Restricted to OFFICER and ADMIN."""
    return await service.get_profile_by_id(student_id)
