"""
Placement Drive management endpoints.
"""
from typing import Annotated
from uuid import UUID

import json
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import UserContext, get_current_user, get_db, require_role
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.placement_drive_repository import PlacementDriveRepository
from app.repositories.student_profile_repository import StudentProfileRepository
from app.schemas.common import PaginatedResponse
from app.schemas.manual_broadcast import ManualBroadcastRequest, ManualBroadcastResponse
from app.schemas.placement_drive import (
    EligibilityCheckResponse,
    PlacementDriveCreate,
    PlacementDriveResponse,
    PlacementDriveStatusUpdate,
    PlacementDriveUpdate,
)
from app.schemas.placement_stage import (
    PlacementStageCreate,
    PlacementStageResponse,
    PlacementStageUpdate,
)
from app.schemas.stage_import import (
    StageImportConfirmRequest,
    StageImportConfirmResponse,
    StageImportPreviewResponse,
    StageQualifiedStudentItem,
)
from app.schemas.student_profile import StudentProfileResponse
from app.services.placement_drive_service import PlacementDriveService
from app.services.placement_stage_service import PlacementStageService
from app.services.registration_service import RegistrationService
from app.services.stage_import_service import StageImportService
from app.repositories.drive_registration_repository import DriveRegistrationRepository
from app.repositories.placement_stage_repository import PlacementStageRepository
from app.repositories.stage_assignment_repository import StageAssignmentRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.analytics_repository import AnalyticsRepository
from app.schemas.analytics import DriveAnalyticsResponse
from app.schemas.drive_registration import DriveRegistrationResponse, DriveRegistrationWithStudentResponse
from app.schemas.stage_assignment import (
    BulkStageStatusRequest,
    StageAssignmentResponse,
    StageAssignmentUpdate,
    StageShortlistRequest,
)
from app.services.analytics_service import AnalyticsService

from app.services.notification_dispatcher import NotificationDispatcher, get_notification_dispatcher

router = APIRouter()


def get_drive_service(
    session: AsyncSession = Depends(get_db),
    dispatcher: NotificationDispatcher = Depends(get_notification_dispatcher),
) -> PlacementDriveService:
    drive_repo = PlacementDriveRepository(session)
    audit_repo = AuditLogRepository(session)
    student_repo = StudentProfileRepository(session)
    return PlacementDriveService(drive_repo, audit_repo, student_repo, dispatcher=dispatcher)


def get_registration_service(
    session: AsyncSession = Depends(get_db),
    dispatcher: NotificationDispatcher = Depends(get_notification_dispatcher),
) -> RegistrationService:
    reg_repo = DriveRegistrationRepository(session)
    audit_repo = AuditLogRepository(session)
    drive_repo = PlacementDriveRepository(session)
    student_repo = StudentProfileRepository(session)
    assignment_repo = StageAssignmentRepository(session)
    drive_service = PlacementDriveService(drive_repo, audit_repo, student_repo, dispatcher=dispatcher)
    return RegistrationService(reg_repo, audit_repo, drive_repo, student_repo, drive_service, assignment_repo, dispatcher=dispatcher)


def get_stage_service(
    session: AsyncSession = Depends(get_db),
    dispatcher: NotificationDispatcher = Depends(get_notification_dispatcher),
) -> PlacementStageService:
    stage_repo = PlacementStageRepository(session)
    assignment_repo = StageAssignmentRepository(session)
    drive_repo = PlacementDriveRepository(session)
    audit_repo = AuditLogRepository(session)
    reg_repo = DriveRegistrationRepository(session)
    return PlacementStageService(stage_repo, assignment_repo, drive_repo, audit_repo, reg_repo, dispatcher=dispatcher)


def get_stage_import_service(
    session: AsyncSession = Depends(get_db),
    dispatcher: NotificationDispatcher = Depends(get_notification_dispatcher),
) -> StageImportService:
    return StageImportService(session, dispatcher=dispatcher)



@router.post("", response_model=PlacementDriveResponse, status_code=201)
async def create_drive(
    data: PlacementDriveCreate,
    current_user: Annotated[UserContext, Depends(require_role("OFFICER", "ADMIN"))],
    service: Annotated[PlacementDriveService, Depends(get_drive_service)],
) -> PlacementDriveResponse:
    """Create a new placement drive (starts as DRAFT). Restricted to OFFICER and ADMIN."""
    return await service.create_drive(data, current_user.user_id)


@router.get("", response_model=PaginatedResponse[PlacementDriveResponse])
async def list_drives(
    current_user: Annotated[UserContext, Depends(get_current_user)],
    service: Annotated[PlacementDriveService, Depends(get_drive_service)],
    status: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[PlacementDriveResponse]:
    """List placement drives. Students cannot see DRAFT drives."""
    skip = (page - 1) * page_size
    is_student = current_user.role == "STUDENT"
    drives, total = await service.list_drives(status=status, skip=skip, limit=page_size, is_student=is_student)
    
    return PaginatedResponse(
        items=list(drives),
        total=total,
        page=page,
        page_size=page_size,
        has_next=(skip + page_size) < total
    )


@router.get("/{drive_id}", response_model=PlacementDriveResponse)
async def get_drive(
    drive_id: UUID,
    current_user: Annotated[UserContext, Depends(get_current_user)],
    service: Annotated[PlacementDriveService, Depends(get_drive_service)],
) -> PlacementDriveResponse:
    """Get drive details."""
    is_student = current_user.role == "STUDENT"
    drive = await service.get_drive(drive_id, current_user.user_id, is_student)
    return drive


@router.patch("/{drive_id}", response_model=PlacementDriveResponse)
async def update_drive(
    drive_id: UUID,
    data: PlacementDriveUpdate,
    current_user: Annotated[UserContext, Depends(require_role("OFFICER", "ADMIN"))],
    service: Annotated[PlacementDriveService, Depends(get_drive_service)],
) -> PlacementDriveResponse:
    """Update drive details. Only allowed in DRAFT status."""
    return await service.update_drive(drive_id, data, current_user.user_id)


@router.delete("/{drive_id}", response_model=dict)
async def delete_drive(
    drive_id: UUID,
    current_user: Annotated[UserContext, Depends(require_role("OFFICER", "ADMIN"))],
    service: Annotated[PlacementDriveService, Depends(get_drive_service)],
) -> dict:
    """Delete/archive a placement drive. Restricted to OFFICER and ADMIN."""
    return await service.delete_drive(drive_id, current_user.user_id)


@router.post("/{drive_id}/status", response_model=PlacementDriveResponse)
async def update_drive_status(
    drive_id: UUID,
    data: PlacementDriveStatusUpdate,
    current_user: Annotated[UserContext, Depends(require_role("OFFICER", "ADMIN"))],
    service: Annotated[PlacementDriveService, Depends(get_drive_service)],
) -> PlacementDriveResponse:
    """Advance drive lifecycle status."""
    return await service.update_drive_status(drive_id, data, current_user.user_id)


@router.get("/{drive_id}/eligibility-check", response_model=EligibilityCheckResponse)
async def check_eligibility(
    drive_id: UUID,
    current_user: Annotated[UserContext, Depends(require_role("STUDENT"))],
    service: Annotated[PlacementDriveService, Depends(get_drive_service)],
) -> EligibilityCheckResponse:
    """Check eligibility of authenticated student for a drive."""
    result = await service.check_eligibility(drive_id, current_user.user_id)
    return EligibilityCheckResponse(
        drive_id=drive_id,
        is_eligible=result.is_eligible,
        reasons=result.reasons
    )


@router.get("/{drive_id}/eligible-students", response_model=PaginatedResponse[StudentProfileResponse])
async def list_eligible_students(
    drive_id: UUID,
    current_user: Annotated[UserContext, Depends(require_role("OFFICER", "ADMIN"))],
    service: Annotated[PlacementDriveService, Depends(get_drive_service)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[StudentProfileResponse]:
    """List students eligible for a drive."""
    skip = (page - 1) * page_size
    students, total = await service.list_eligible_students(drive_id, skip=skip, limit=page_size)
    
    return PaginatedResponse(
        items=list(students),
        total=total,
        page=page,
        page_size=page_size,
        has_next=(skip + page_size) < total
    )


@router.post("/{drive_id}/register", response_model=DriveRegistrationResponse, status_code=201)
async def register_student(
    drive_id: UUID,
    current_user: Annotated[UserContext, Depends(require_role("STUDENT"))],
    service: Annotated[RegistrationService, Depends(get_registration_service)],
) -> DriveRegistrationResponse:
    """Register the authenticated student for a drive."""
    return await service.register_student(drive_id, current_user.user_id)


@router.get("/{drive_id}/registrations", response_model=PaginatedResponse[DriveRegistrationWithStudentResponse])
async def list_registrations(
    drive_id: UUID,
    current_user: Annotated[UserContext, Depends(require_role("OFFICER", "ADMIN"))],
    service: Annotated[RegistrationService, Depends(get_registration_service)],
    status: str | None = None,
    branch: str | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[DriveRegistrationWithStudentResponse]:
    """List registrations for a drive."""
    skip = (page - 1) * page_size
    registrations, total = await service.list_drive_registrations(
        drive_id, skip=skip, limit=page_size, status=status, branch=branch, search=search
    )
    
    return PaginatedResponse(
        items=list(registrations),
        total=total,
        page=page,
        page_size=page_size,
        has_next=(skip + page_size) < total
    )
@router.post("/{drive_id}/stages", response_model=PlacementStageResponse, status_code=201)
async def create_stage(
    drive_id: UUID,
    data: PlacementStageCreate,
    current_user: Annotated[UserContext, Depends(require_role("OFFICER", "ADMIN"))],
    service: Annotated[PlacementStageService, Depends(get_stage_service)],
) -> PlacementStageResponse:
    """Create a placement stage."""
    return await service.create_stage(drive_id, data, current_user.user_id)


@router.get("/{drive_id}/stages", response_model=list[PlacementStageResponse])
async def list_stages(
    drive_id: UUID,
    current_user: Annotated[UserContext, Depends(get_current_user)],
    service: Annotated[PlacementStageService, Depends(get_stage_service)],
) -> list[PlacementStageResponse]:
    """List stages for a drive. Students only see published stages they are assigned to."""
    is_student = current_user.role == "STUDENT"
    return list(await service.list_stages(drive_id, current_user.user_id, is_student))


@router.patch("/{drive_id}/stages/{stage_id}", response_model=PlacementStageResponse)
async def update_stage(
    drive_id: UUID,
    stage_id: UUID,
    data: PlacementStageUpdate,
    current_user: Annotated[UserContext, Depends(require_role("OFFICER", "ADMIN"))],
    service: Annotated[PlacementStageService, Depends(get_stage_service)],
) -> PlacementStageResponse:
    """Update a stage."""
    return await service.update_stage(drive_id, stage_id, data, current_user.user_id)


@router.post("/{drive_id}/stages/{stage_id}/publish", response_model=dict)
async def publish_stage(
    drive_id: UUID,
    stage_id: UUID,
    current_user: Annotated[UserContext, Depends(require_role("OFFICER", "ADMIN"))],
    service: Annotated[PlacementStageService, Depends(get_stage_service)],
) -> dict:
    """Publish a stage."""
    return await service.publish_stage(drive_id, stage_id, current_user.user_id)


@router.post("/{drive_id}/stages/{stage_id}/shortlist", response_model=dict, status_code=201)
async def shortlist_students(
    drive_id: UUID,
    stage_id: UUID,
    data: StageShortlistRequest,
    current_user: Annotated[UserContext, Depends(require_role("OFFICER", "ADMIN"))],
    service: Annotated[PlacementStageService, Depends(get_stage_service)],
) -> dict:
    """Shortlist students for a stage."""
    return await service.shortlist_students(drive_id, stage_id, data, current_user.user_id)


@router.post("/{drive_id}/stages/{stage_id}/bulk-status", response_model=dict)
async def bulk_update_stage_status(
    drive_id: UUID,
    stage_id: UUID,
    data: BulkStageStatusRequest,
    current_user: Annotated[UserContext, Depends(require_role("OFFICER", "ADMIN"))],
    service: Annotated[PlacementStageService, Depends(get_stage_service)],
) -> dict:
    """Bulk update candidate assignment statuses for a stage."""
    return await service.bulk_update_status(drive_id, stage_id, data, current_user.user_id)


@router.patch("/{drive_id}/stages/{stage_id}/assignments/{student_id}", response_model=StageAssignmentResponse)
async def update_stage_assignment(
    drive_id: UUID,
    stage_id: UUID,
    student_id: UUID,
    data: StageAssignmentUpdate,
    current_user: Annotated[UserContext, Depends(require_role("OFFICER", "ADMIN"))],
    service: Annotated[PlacementStageService, Depends(get_stage_service)],
) -> StageAssignmentResponse:
    """Update a student's stage assignment result/status."""
    return await service.update_assignment(drive_id, stage_id, student_id, data, current_user.user_id)


@router.post("/{drive_id}/stages/{stage_id}/publish-results", response_model=dict)
async def publish_results(
    drive_id: UUID,
    stage_id: UUID,
    current_user: Annotated[UserContext, Depends(require_role("OFFICER", "ADMIN"))],
    service: Annotated[PlacementStageService, Depends(get_stage_service)],
) -> dict:
    """Publish results for a stage, notifying all assigned students."""
    return await service.publish_results(drive_id, stage_id, current_user.user_id)


@router.post("/{drive_id}/stages/{stage_id}/qualified/preview", response_model=StageImportPreviewResponse)
async def preview_stage_qualified_import(
    drive_id: UUID,
    stage_id: UUID,
    file: UploadFile = File(...),
    custom_mapping: str | None = Form(None),
    current_user: Annotated[UserContext, Depends(require_role("OFFICER", "ADMIN"))] = None,
    service: Annotated[StageImportService, Depends(get_stage_import_service)] = None,
) -> StageImportPreviewResponse:
    """Preview company-provided qualified student list for a drive stage."""
    filename = file.filename or "qualified.xlsx"
    if not (
        filename.lower().endswith(".xlsx")
        or filename.lower().endswith(".xls")
        or filename.lower().endswith(".csv")
    ):
        raise HTTPException(
            status_code=400,
            detail="Only .xlsx, .xls, or .csv files are supported.",
        )

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    mapping_dict = None
    if custom_mapping:
        try:
            mapping_dict = json.loads(custom_mapping)
        except Exception:
            pass

    return await service.preview_stage_qualified_import(
        drive_id=drive_id,
        stage_id=stage_id,
        file_bytes=file_bytes,
        filename=filename,
        custom_mapping=mapping_dict,
    )


@router.post("/{drive_id}/stages/{stage_id}/qualified/confirm", response_model=StageImportConfirmResponse)
async def confirm_stage_qualified_import(
    drive_id: UUID,
    stage_id: UUID,
    data: StageImportConfirmRequest,
    current_user: Annotated[UserContext, Depends(require_role("OFFICER", "ADMIN"))] = None,
    service: Annotated[StageImportService, Depends(get_stage_import_service)] = None,
) -> StageImportConfirmResponse:
    """Confirm and commit qualified students to the drive stage."""
    return await service.confirm_stage_qualified_import(
        drive_id=drive_id,
        stage_id=stage_id,
        request=data,
        current_user_id=current_user.user_id,
    )


@router.get("/{drive_id}/stages/{stage_id}/qualified/students", response_model=list[StageQualifiedStudentItem])
async def list_stage_qualified_students(
    drive_id: UUID,
    stage_id: UUID,
    current_user: Annotated[UserContext, Depends(require_role("OFFICER", "ADMIN"))] = None,
    service: Annotated[StageImportService, Depends(get_stage_import_service)] = None,
) -> list[StageQualifiedStudentItem]:
    """List all qualified students assigned to a specific drive stage."""
    return await service.list_stage_qualified_students(drive_id, stage_id)


@router.post("/{drive_id}/notify", response_model=ManualBroadcastResponse, status_code=202)
async def broadcast_drive_notification(
    drive_id: UUID,
    data: ManualBroadcastRequest,
    current_user: Annotated[UserContext, Depends(require_role("OFFICER", "ADMIN"))],
    service: Annotated[PlacementDriveService, Depends(get_drive_service)],
) -> ManualBroadcastResponse:
    """Broadcast a manual notification to selected audience for a drive."""
    return await service.broadcast_notification(drive_id, data, current_user.user_id)


def get_analytics_service(
    session: AsyncSession = Depends(get_db),
) -> AnalyticsService:
    analytics_repo = AnalyticsRepository(session)
    drive_repo = PlacementDriveRepository(session)
    student_repo = StudentProfileRepository(session)
    return AnalyticsService(analytics_repo, drive_repo, student_repo)


@router.get("/{drive_id}/analytics", response_model=DriveAnalyticsResponse)
async def get_drive_analytics(
    drive_id: UUID,
    current_user: Annotated[UserContext, Depends(require_role("OFFICER", "ADMIN"))],
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> DriveAnalyticsResponse:
    """Get aggregate recruitment funnel and branch analytics for a placement drive."""
    return await service.get_drive_analytics(drive_id)


