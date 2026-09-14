"""
Student Profile endpoints for officers.
"""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.dependencies import UserContext, get_db, require_role, get_storage_service
from app.core.limiter import limiter
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.student_profile_repository import StudentProfileRepository
from app.schemas.common import PaginatedResponse
from app.schemas.student_profile import StudentProfileResponse
from app.services.student_profile_service import StudentProfileService
from app.services.storage_service import StorageService

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
    batch_year: int | None = None,
    min_cgpa: float | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[StudentProfileResponse]:
    """List all student profiles. Restricted to OFFICER and ADMIN."""
    skip = (page - 1) * page_size
    students, total = await service.list_students(
        skip=skip, 
        limit=page_size, 
        branch_code=branch_code,
        batch_year=batch_year,
        min_cgpa=min_cgpa,
        search=search
    )
    
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

@router.get("/students/{student_id}/resume-download-url")
@limiter.limit(get_settings().rate_limit_resume_download)
async def get_resume_download_url(
    request: Request,
    student_id: UUID,
    current_user: Annotated[UserContext, Depends(require_role("OFFICER", "ADMIN"))],
    service: Annotated[StudentProfileService, Depends(get_profile_service)],
    storage: Annotated[StorageService, Depends(get_storage_service)],
) -> dict[str, str]:
    """Generate a signed GCS URL for resume download. Logs the access."""
    profile = await service.get_profile_by_id(student_id)
    
    if not profile.resume_gcs_path:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Student has no resume uploaded.")
        
    service._log_audit(
        user_id=current_user.user_id,
        action="RESUME_DOWNLOADED",
        entity_id=student_id,
        old_state=None,
        new_state={"resume_path": profile.resume_gcs_path}
    )
    await service.profile_repo.session.commit()
    
    settings = get_settings()
    url = await storage.generate_download_url(
        object_path=profile.resume_gcs_path,
        expires_in_seconds=settings.resume_url_expires_in
    )
    
    return {"url": url}
