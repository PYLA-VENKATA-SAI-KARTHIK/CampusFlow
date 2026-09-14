"""
Preparation Hub API endpoints.
"""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import UserContext, get_db, require_role
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.preparation_repository import PreparationRepository
from app.schemas.common import PaginatedResponse
from app.schemas.preparation import (
    OfficerCreateMaterialRequest,
    OfficerReviewSubmissionRequest,
    PreparationCategoryResponse,
    PreparationMaterialResponse,
    PreparationRoleResponse,
    RoleRoadmapResponse,
    StudentSuggestMaterialRequest,
)
from app.services.preparation_service import PreparationService

router = APIRouter()


def get_preparation_service(session: AsyncSession = Depends(get_db)) -> PreparationService:
    prep_repo = PreparationRepository(session)
    audit_repo = AuditLogRepository(session)
    return PreparationService(prep_repo, audit_repo)


# =========================================================================
# PUBLIC AUTHENTICATED & STUDENT ENDPOINTS (/preparation/*)
# =========================================================================


@router.get("/roles", response_model=list[PreparationRoleResponse])
async def list_roles(
    current_user: Annotated[UserContext, Depends(require_role("STUDENT", "OFFICER", "ADMIN"))],
    service: Annotated[PreparationService, Depends(get_preparation_service)],
) -> list[PreparationRoleResponse]:
    """List all active preparation roles."""
    roles = await service.get_roles()
    return list(roles)


@router.get("/categories", response_model=list[PreparationCategoryResponse])
async def list_categories(
    current_user: Annotated[UserContext, Depends(require_role("STUDENT", "OFFICER", "ADMIN"))],
    service: Annotated[PreparationService, Depends(get_preparation_service)],
) -> list[PreparationCategoryResponse]:
    """List all categories with nested topics."""
    categories = await service.get_categories_with_topics()
    return list(categories)


@router.get("/materials", response_model=PaginatedResponse[PreparationMaterialResponse])
async def list_materials(
    current_user: Annotated[UserContext, Depends(require_role("STUDENT", "OFFICER", "ADMIN"))],
    service: Annotated[PreparationService, Depends(get_preparation_service)],
    category_id: UUID | None = None,
    topic_id: UUID | None = None,
    role_id: UUID | None = None,
    difficulty: str | None = None,
    material_type: str | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[PreparationMaterialResponse]:
    """List approved preparation materials with optional topic, category, role, and keyword filters."""
    materials, total = await service.get_materials(
        category_id=category_id,
        topic_id=topic_id,
        role_id=role_id,
        difficulty=difficulty,
        material_type=material_type,
        search=search,
        page=page,
        page_size=page_size,
    )
    skip = (page - 1) * page_size
    return PaginatedResponse(
        items=list(materials),
        total=total,
        page=page,
        page_size=page_size,
        has_next=(skip + page_size) < total,
    )


@router.get("/roles/{role_code}/roadmap", response_model=RoleRoadmapResponse)
async def get_role_roadmap(
    role_code: str,
    current_user: Annotated[UserContext, Depends(require_role("STUDENT", "OFFICER", "ADMIN"))],
    service: Annotated[PreparationService, Depends(get_preparation_service)],
) -> RoleRoadmapResponse:
    """Get the recommended topic roadmap and resource counts for a target role."""
    return await service.get_role_roadmap(role_code)


@router.post("/suggest", response_model=PreparationMaterialResponse, status_code=201)
async def suggest_material(
    data: StudentSuggestMaterialRequest,
    current_user: Annotated[UserContext, Depends(require_role("STUDENT"))],
    service: Annotated[PreparationService, Depends(get_preparation_service)],
) -> PreparationMaterialResponse:
    """Submit a material suggestion for review (Status: PENDING)."""
    return await service.suggest_material(current_user.user_id, data)


@router.get("/my-suggestions", response_model=PaginatedResponse[PreparationMaterialResponse])
async def list_my_suggestions(
    current_user: Annotated[UserContext, Depends(require_role("STUDENT"))],
    service: Annotated[PreparationService, Depends(get_preparation_service)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[PreparationMaterialResponse]:
    """List material suggestions submitted by the authenticated student."""
    materials, total = await service.get_student_suggestions(
        user_id=current_user.user_id, page=page, page_size=page_size
    )
    skip = (page - 1) * page_size
    return PaginatedResponse(
        items=list(materials),
        total=total,
        page=page,
        page_size=page_size,
        has_next=(skip + page_size) < total,
    )


# =========================================================================
# OFFICER / ADMIN REVIEW & CREATION ENDPOINTS
# =========================================================================


@router.get("/officers/submissions", response_model=PaginatedResponse[PreparationMaterialResponse])
async def list_pending_submissions(
    current_user: Annotated[UserContext, Depends(require_role("OFFICER", "ADMIN"))],
    service: Annotated[PreparationService, Depends(get_preparation_service)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[PreparationMaterialResponse]:
    """List pending student material submissions awaiting review. Restricted to OFFICER and ADMIN."""
    materials, total = await service.get_pending_submissions(page=page, page_size=page_size)
    skip = (page - 1) * page_size
    return PaginatedResponse(
        items=list(materials),
        total=total,
        page=page,
        page_size=page_size,
        has_next=(skip + page_size) < total,
    )


@router.post("/officers/submissions/{material_id}/review", response_model=PreparationMaterialResponse)
async def review_submission(
    material_id: UUID,
    data: OfficerReviewSubmissionRequest,
    current_user: Annotated[UserContext, Depends(require_role("OFFICER", "ADMIN"))],
    service: Annotated[PreparationService, Depends(get_preparation_service)],
) -> PreparationMaterialResponse:
    """Approve or reject a submitted preparation material with audit logging."""
    return await service.review_submission(
        material_id=material_id, reviewer_user_id=current_user.user_id, data=data
    )


@router.post("/officers/materials", response_model=PreparationMaterialResponse, status_code=201)
async def create_material_as_officer(
    data: OfficerCreateMaterialRequest,
    current_user: Annotated[UserContext, Depends(require_role("OFFICER", "ADMIN"))],
    service: Annotated[PreparationService, Depends(get_preparation_service)],
) -> PreparationMaterialResponse:
    """Directly create and publish an approved preparation material with audit logging."""
    return await service.create_material_as_officer(
        creator_user_id=current_user.user_id, data=data
    )


@router.delete("/officers/materials/{material_id}", status_code=204)
async def delete_material_as_officer(
    material_id: UUID,
    current_user: Annotated[UserContext, Depends(require_role("OFFICER", "ADMIN"))],
    service: Annotated[PreparationService, Depends(get_preparation_service)],
) -> None:
    """Delete an approved preparation material with audit logging. Restricted to OFFICER and ADMIN."""
    await service.delete_material_as_officer(
        material_id=material_id, user_id=current_user.user_id
    )

