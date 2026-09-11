"""
Admin API — ADMIN role only.

Endpoints:
  GET    /admin/users                    — List users (paginated, filterable)
  POST   /admin/users                    — Create OFFICER or ADMIN user
  PATCH  /admin/users/{user_id}          — Update role / is_active / full_name
  POST   /admin/students/bulk-import     — CSV upload → partial-success processing
  GET    /admin/audit-logs               — Read-only filterable audit log listing

All endpoints enforce require_role("ADMIN") server-side.
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import UserContext, get_db, require_role
from app.core.email import create_email_service
from app.core.config import get_settings
from app.schemas.admin import (
    AdminAuditLogListParams,
    AdminAuditLogResponse,
    AdminCreateUserRequest,
    AdminUpdateUserRequest,
    AdminUserListParams,
    AdminUserResponse,
    BulkImportResponse,
)
from app.schemas.common import PaginatedResponse
from app.services.admin_service import AdminService

router = APIRouter()


def _get_client_ip(request: Request) -> str | None:
    """Extract client IP from X-Forwarded-For or direct connection."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


def _get_admin_service(session: AsyncSession) -> AdminService:
    settings = get_settings()
    email_service = create_email_service(
        provider=settings.email_provider,
        sendgrid_api_key=settings.sendgrid_api_key,
        sendgrid_from_email=settings.sendgrid_from_email,
        sendgrid_from_name=settings.sendgrid_from_name,
    )
    return AdminService(session=session, email_service=email_service)


# ---------------------------------------------------------------------------
# GET /admin/users
# ---------------------------------------------------------------------------


@router.get("/users", response_model=PaginatedResponse[AdminUserResponse])
async def list_users(
    request: Request,
    current_user: UserContext = Depends(require_role("ADMIN")),
    db: AsyncSession = Depends(get_db),
    role: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    service = _get_admin_service(db)
    params = AdminUserListParams(
        role=role, is_active=is_active, search=search,
        page=page, page_size=page_size,
    )
    return await service.list_users(params)


# ---------------------------------------------------------------------------
# POST /admin/users
# ---------------------------------------------------------------------------


@router.post("/users", response_model=AdminUserResponse, status_code=201)
async def create_user(
    data: AdminCreateUserRequest,
    request: Request,
    current_user: UserContext = Depends(require_role("ADMIN")),
    db: AsyncSession = Depends(get_db),
):
    service = _get_admin_service(db)
    return await service.create_user(
        data=data,
        performed_by_user_id=current_user.user_id,
        ip_address=_get_client_ip(request),
    )


# ---------------------------------------------------------------------------
# PATCH /admin/users/{user_id}
# ---------------------------------------------------------------------------


@router.patch("/users/{user_id}", response_model=AdminUserResponse)
async def update_user(
    user_id: UUID,
    data: AdminUpdateUserRequest,
    request: Request,
    current_user: UserContext = Depends(require_role("ADMIN")),
    db: AsyncSession = Depends(get_db),
):
    service = _get_admin_service(db)
    return await service.update_user(
        user_id=user_id,
        data=data,
        performed_by_user_id=current_user.user_id,
        ip_address=_get_client_ip(request),
    )


# ---------------------------------------------------------------------------
# POST /admin/students/bulk-import
# ---------------------------------------------------------------------------


@router.post("/students/bulk-import", response_model=BulkImportResponse, status_code=202)
async def bulk_import_students(
    request: Request,
    file: UploadFile = File(...),
    current_user: UserContext = Depends(require_role("ADMIN")),
    db: AsyncSession = Depends(get_db),
):
    contents = await file.read()
    csv_content = contents.decode("utf-8")
    service = _get_admin_service(db)
    return await service.bulk_import_students(
        csv_content=csv_content,
        performed_by_user_id=current_user.user_id,
        ip_address=_get_client_ip(request),
    )


# ---------------------------------------------------------------------------
# GET /admin/audit-logs
# ---------------------------------------------------------------------------


@router.get("/audit-logs", response_model=PaginatedResponse[AdminAuditLogResponse])
async def list_audit_logs(
    request: Request,
    current_user: UserContext = Depends(require_role("ADMIN")),
    db: AsyncSession = Depends(get_db),
    user_id: UUID | None = Query(default=None),
    entity_type: str | None = Query(default=None),
    action: str | None = Query(default=None),
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    from datetime import datetime

    parsed_start = datetime.fromisoformat(start_date) if start_date else None
    parsed_end = datetime.fromisoformat(end_date) if end_date else None

    service = _get_admin_service(db)
    params = AdminAuditLogListParams(
        user_id=user_id, entity_type=entity_type, action=action,
        start_date=parsed_start, end_date=parsed_end,
        page=page, page_size=page_size,
    )
    return await service.list_audit_logs(params)
