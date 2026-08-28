"""
Student Profile endpoints for students.
"""
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import UserContext, get_db, require_role
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.student_profile_repository import StudentProfileRepository
from app.schemas.student_profile import StudentProfileResponse, StudentProfileUpdate
from app.services.student_profile_service import StudentProfileService

router = APIRouter()


def get_profile_service(session: AsyncSession = Depends(get_db)) -> StudentProfileService:
    profile_repo = StudentProfileRepository(session)
    audit_repo = AuditLogRepository(session)
    return StudentProfileService(profile_repo, audit_repo)


@router.get("/me", response_model=StudentProfileResponse)
async def get_my_profile(
    current_user: Annotated[UserContext, Depends(require_role("STUDENT"))],
    service: Annotated[StudentProfileService, Depends(get_profile_service)],
) -> StudentProfileResponse:
    """Get the currently authenticated student's profile."""
    return await service.get_profile_by_user_id(current_user.user_id)


@router.patch("/me", response_model=StudentProfileResponse)
async def update_my_profile(
    data: StudentProfileUpdate,
    current_user: Annotated[UserContext, Depends(require_role("STUDENT"))],
    service: Annotated[StudentProfileService, Depends(get_profile_service)],
) -> StudentProfileResponse:
    """Update the currently authenticated student's profile."""
    return await service.update_my_profile(current_user.user_id, data)
