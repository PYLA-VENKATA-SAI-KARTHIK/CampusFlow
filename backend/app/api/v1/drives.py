"""
Placement Drive management endpoints.
"""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import UserContext, get_current_user, get_db, require_role
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.placement_drive_repository import PlacementDriveRepository
from app.schemas.common import PaginatedResponse
from app.schemas.placement_drive import (
    PlacementDriveCreate,
    PlacementDriveResponse,
    PlacementDriveStatusUpdate,
    PlacementDriveUpdate,
)
from app.services.placement_drive_service import PlacementDriveService

router = APIRouter()


def get_drive_service(session: AsyncSession = Depends(get_db)) -> PlacementDriveService:
    drive_repo = PlacementDriveRepository(session)
    audit_repo = AuditLogRepository(session)
    return PlacementDriveService(drive_repo, audit_repo)


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
    drive = await service.get_drive(drive_id)
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


@router.post("/{drive_id}/status", response_model=PlacementDriveResponse)
async def update_drive_status(
    drive_id: UUID,
    data: PlacementDriveStatusUpdate,
    current_user: Annotated[UserContext, Depends(require_role("OFFICER", "ADMIN"))],
    service: Annotated[PlacementDriveService, Depends(get_drive_service)],
) -> PlacementDriveResponse:
    """Advance drive lifecycle status."""
    return await service.update_drive_status(drive_id, data, current_user.user_id)
