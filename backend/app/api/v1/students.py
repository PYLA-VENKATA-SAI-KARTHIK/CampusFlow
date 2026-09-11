"""
Student Profile endpoints for students.
"""
from typing import Annotated

from uuid import uuid4
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import UserContext, get_db, require_role, get_storage_service
from app.core.config import get_settings
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.student_profile_repository import StudentProfileRepository
from app.schemas.student_profile import (
    StudentProfileResponse,
    StudentProfileUpdate,
    ResumeUploadUrlResponse,
    ResumeConfirmRequest
)
from app.services.student_profile_service import StudentProfileService
from app.services.storage_service import StorageService
from app.services.registration_service import RegistrationService
from app.services.placement_drive_service import PlacementDriveService
from app.repositories.drive_registration_repository import DriveRegistrationRepository
from app.repositories.placement_drive_repository import PlacementDriveRepository
from app.repositories.stage_assignment_repository import StageAssignmentRepository
from app.schemas.drive_registration import StudentApplicationResponse
from app.schemas.common import PaginatedResponse
from fastapi import Query

router = APIRouter()


def get_profile_service(session: AsyncSession = Depends(get_db)) -> StudentProfileService:
    profile_repo = StudentProfileRepository(session)
    audit_repo = AuditLogRepository(session)
    return StudentProfileService(profile_repo, audit_repo)


def get_registration_service(session: AsyncSession = Depends(get_db)) -> RegistrationService:
    reg_repo = DriveRegistrationRepository(session)
    audit_repo = AuditLogRepository(session)
    drive_repo = PlacementDriveRepository(session)
    student_repo = StudentProfileRepository(session)
    assignment_repo = StageAssignmentRepository(session)
    drive_service = PlacementDriveService(drive_repo, audit_repo, student_repo)
    return RegistrationService(reg_repo, audit_repo, drive_repo, student_repo, drive_service, assignment_repo)


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


@router.get("/me/resume-upload-url", response_model=ResumeUploadUrlResponse)
async def get_resume_upload_url(
    current_user: Annotated[UserContext, Depends(require_role("STUDENT"))],
    service: Annotated[StudentProfileService, Depends(get_profile_service)],
    storage: Annotated[StorageService, Depends(get_storage_service)],
) -> ResumeUploadUrlResponse:
    """Generate a signed URL to upload a resume PDF."""
    await service.get_profile_by_user_id(current_user.user_id)
    
    settings = get_settings()
    object_path = f"resumes/{current_user.user_id}/{uuid4()}.pdf"
    
    upload_url = await storage.generate_upload_url(
        object_path=object_path,
        content_type="application/pdf",
        max_size_bytes=settings.resume_max_size_bytes,
        expires_in_seconds=settings.resume_url_expires_in,
    )
    
    return ResumeUploadUrlResponse(
        upload_url=upload_url,
        object_path=object_path,
        expires_in=settings.resume_url_expires_in
    )


@router.post("/me/resume-confirm", response_model=StudentProfileResponse)
async def confirm_resume_upload(
    request: ResumeConfirmRequest,
    current_user: Annotated[UserContext, Depends(require_role("STUDENT"))],
    service: Annotated[StudentProfileService, Depends(get_profile_service)],
    storage: Annotated[StorageService, Depends(get_storage_service)],
) -> StudentProfileResponse:
    """Confirm resume upload was successful and update profile."""
    
    # 1. Ensure object path is valid and belongs to the user
    expected_prefix = f"resumes/{current_user.user_id}/"
    if (
        not request.object_path.startswith(expected_prefix)
        or not request.object_path.endswith(".pdf")
        or ".." in request.object_path
    ):
        raise HTTPException(status_code=422, detail="Invalid object path.")

    # 2. Verify object in storage
    metadata = await storage.verify_object(request.object_path)
    if not metadata:
        raise HTTPException(status_code=404, detail="Resume object not found in storage.")
        
    if metadata.get("content_type") != "application/pdf":
        raise HTTPException(status_code=422, detail="Resume must be a PDF.")
        
    settings = get_settings()
    if metadata.get("size", 0) > settings.resume_max_size_bytes:
        raise HTTPException(status_code=422, detail="Resume exceeds maximum allowed size.")

    # 3. Update profile
    profile = await service.get_profile_by_user_id(current_user.user_id)
    
    old_state = {"resume_gcs_path": profile.resume_gcs_path}
    
    profile.resume_gcs_path = request.object_path
    profile.resume_uploaded_at = datetime.now(timezone.utc)
    
    new_state = {"resume_gcs_path": profile.resume_gcs_path}
    
    service._log_audit(
        user_id=current_user.user_id,
        action="RESUME_UPLOADED",
        entity_id=profile.id,
        old_state=old_state,
        new_state=new_state
    )
    
    await service.profile_repo.session.commit()
    await service.profile_repo.session.refresh(profile)
    return profile


@router.get("/me/resume-download-url")
async def get_my_resume_download_url(
    current_user: Annotated[UserContext, Depends(require_role("STUDENT"))],
    service: Annotated[StudentProfileService, Depends(get_profile_service)],
    storage: Annotated[StorageService, Depends(get_storage_service)],
) -> dict[str, str]:
    """Generate a signed GET URL for the student's own resume."""
    profile = await service.get_profile_by_user_id(current_user.user_id)
    
    if not profile.resume_gcs_path:
        raise HTTPException(status_code=404, detail="No resume uploaded.")
        
    settings = get_settings()
    url = await storage.generate_download_url(
        object_path=profile.resume_gcs_path,
        expires_in_seconds=settings.resume_url_expires_in
    )
    return {"url": url}


@router.get("/me/applications", response_model=PaginatedResponse[StudentApplicationResponse])
async def list_my_applications(
    current_user: Annotated[UserContext, Depends(require_role("STUDENT"))],
    service: Annotated[RegistrationService, Depends(get_registration_service)],
    status: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[StudentApplicationResponse]:
    """List the authenticated student's registrations and current status."""
    skip = (page - 1) * page_size
    applications, total = await service.list_student_applications(current_user.user_id, skip=skip, limit=page_size, status=status)
    
    return PaginatedResponse(
        items=list(applications),
        total=total,
        page=page,
        page_size=page_size,
        has_next=(skip + page_size) < total
    )
