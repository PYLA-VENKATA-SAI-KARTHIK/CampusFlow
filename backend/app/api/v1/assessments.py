"""
Practice Assessment Engine API routes.
"""
from __future__ import annotations

from typing import Annotated, Sequence
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import UserContext, get_current_user, get_db, require_role
from app.repositories.assessment_repository import AssessmentRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.schemas.assessment import (
    AssessmentAdminDetail,
    AssessmentAssignRequest,
    AssessmentAssignmentResponse,
    AssessmentCreate,
    AssessmentResultResponse,
    AssessmentStudentPreview,
    AssessmentSummary,
    AssessmentUpdate,
    OfficerAssessmentResultsView,
    QuestionAdminView,
    QuestionCreate,
    QuestionUpdate,
    SaveProgressRequest,
    StartAttemptResponse,
    SubmitAttemptRequest,
)
from app.services.assessment_service import AssessmentService
from app.services.notification_dispatcher import get_notification_dispatcher

router = APIRouter()


def get_assessment_service(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> AssessmentService:
    assessment_repo = AssessmentRepository(session)
    audit_repo = AuditLogRepository(session)
    dispatcher = get_notification_dispatcher()
    return AssessmentService(
        assessment_repo=assessment_repo,
        audit_repo=audit_repo,
        dispatcher=dispatcher,
    )


# ---------------------------------------------------------------------------
# Student Specific Endpoints (Must be above path parameter {assessment_id})
# ---------------------------------------------------------------------------

@router.get(
    "/assigned",
    response_model=list[AssessmentAssignmentResponse],
    summary="List assessments assigned to the current student",
)
async def get_my_assigned_assessments(
    current_user: Annotated[UserContext, Depends(require_role("STUDENT"))],
    service: Annotated[AssessmentService, Depends(get_assessment_service)],
    status: str | None = Query(default=None, description="Filter by status: ASSIGNED, IN_PROGRESS, COMPLETED"),
) -> list[AssessmentAssignmentResponse]:
    return await service.get_student_assigned_assessments(
        student_user_id=UUID(current_user.user_id), status=status
    )


@router.get(
    "/my-history",
    response_model=list[AssessmentResultResponse],
    summary="List past assessment results for current student",
)
async def get_my_assessment_history(
    current_user: Annotated[UserContext, Depends(require_role("STUDENT"))],
    service: Annotated[AssessmentService, Depends(get_assessment_service)],
) -> list[AssessmentResultResponse]:
    return await service.get_student_history(student_user_id=UUID(current_user.user_id))


@router.get(
    "/attempts/{attempt_id}/active",
    response_model=StartAttemptResponse,
    summary="Get active attempt state and questions (Student only)",
)
async def get_active_attempt(
    attempt_id: UUID,
    current_user: Annotated[UserContext, Depends(require_role("STUDENT"))],
    service: Annotated[AssessmentService, Depends(get_assessment_service)],
) -> StartAttemptResponse:
    return await service.get_active_attempt(
        attempt_id=attempt_id,
        student_user_id=UUID(current_user.user_id),
    )


@router.post(
    "/attempts/{attempt_id}/save-progress",
    status_code=status.HTTP_200_OK,
    summary="Autosave student answers for an in-progress attempt",
)
async def save_attempt_progress(
    attempt_id: UUID,
    payload: SaveProgressRequest,
    current_user: Annotated[UserContext, Depends(require_role("STUDENT"))],
    service: Annotated[AssessmentService, Depends(get_assessment_service)],
):
    return await service.save_progress(
        attempt_id=attempt_id,
        student_user_id=UUID(current_user.user_id),
        payload=payload,
    )


@router.post(
    "/attempts/{attempt_id}/submit",
    response_model=AssessmentResultResponse,
    summary="Submit attempt for authoritative server evaluation",
)
async def submit_attempt(
    attempt_id: UUID,
    current_user: Annotated[UserContext, Depends(require_role("STUDENT"))],
    service: Annotated[AssessmentService, Depends(get_assessment_service)],
    payload: SubmitAttemptRequest | None = None,
) -> AssessmentResultResponse:
    return await service.submit_assessment_attempt(
        attempt_id=attempt_id,
        student_user_id=UUID(current_user.user_id),
        payload=payload,
    )


@router.get(
    "/attempts/{attempt_id}/result",
    response_model=AssessmentResultResponse,
    summary="Get evaluated result and post-submission review",
)
async def get_attempt_result(
    attempt_id: UUID,
    current_user: Annotated[UserContext, Depends(get_current_user)],
    service: Annotated[AssessmentService, Depends(get_assessment_service)],
) -> AssessmentResultResponse:
    return await service.get_attempt_result(
        attempt_id=attempt_id,
        current_user_id=UUID(current_user.user_id),
        current_user_role=current_user.role,
    )


# ---------------------------------------------------------------------------
# Officer / Admin Management Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "",
    response_model=AssessmentSummary,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new draft practice assessment",
)
async def create_assessment(
    payload: AssessmentCreate,
    current_user: Annotated[UserContext, Depends(require_role("OFFICER", "ADMIN"))],
    service: Annotated[AssessmentService, Depends(get_assessment_service)],
) -> AssessmentSummary:
    return await service.create_assessment(
        payload=payload, user_id=UUID(current_user.user_id)
    )


@router.get(
    "",
    response_model=list[AssessmentSummary],
    summary="List all assessments (Officer/Admin)",
)
async def list_assessments(
    current_user: Annotated[UserContext, Depends(require_role("OFFICER", "ADMIN"))],
    service: Annotated[AssessmentService, Depends(get_assessment_service)],
    status: str | None = Query(default=None),
    category_id: UUID | None = Query(default=None),
    topic_id: UUID | None = Query(default=None),
    role_id: UUID | None = Query(default=None),
    placement_drive_id: UUID | None = Query(default=None),
    difficulty: str | None = Query(default=None),
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> list[AssessmentSummary]:
    items, _ = await service.list_assessments(
        status=status,
        category_id=category_id,
        topic_id=topic_id,
        role_id=role_id,
        placement_drive_id=placement_drive_id,
        difficulty=difficulty,
        search=search,
        page=page,
        page_size=page_size,
    )
    return items


@router.get(
    "/{assessment_id}",
    response_model=AssessmentAdminDetail,
    summary="Get assessment details and questions (Officer/Admin)",
)
async def get_assessment_admin(
    assessment_id: UUID,
    current_user: Annotated[UserContext, Depends(require_role("OFFICER", "ADMIN"))],
    service: Annotated[AssessmentService, Depends(get_assessment_service)],
) -> AssessmentAdminDetail:
    return await service.get_assessment_admin(assessment_id=assessment_id)


@router.patch(
    "/{assessment_id}",
    response_model=AssessmentSummary,
    summary="Update assessment metadata (Draft only)",
)
async def update_assessment(
    assessment_id: UUID,
    payload: AssessmentUpdate,
    current_user: Annotated[UserContext, Depends(require_role("OFFICER", "ADMIN"))],
    service: Annotated[AssessmentService, Depends(get_assessment_service)],
) -> AssessmentSummary:
    return await service.update_assessment(
        assessment_id=assessment_id,
        payload=payload,
        user_id=UUID(current_user.user_id),
    )


@router.post(
    "/{assessment_id}/questions",
    response_model=QuestionAdminView,
    status_code=status.HTTP_201_CREATED,
    summary="Add a question to a draft assessment",
)
async def add_question(
    assessment_id: UUID,
    payload: QuestionCreate,
    current_user: Annotated[UserContext, Depends(require_role("OFFICER", "ADMIN"))],
    service: Annotated[AssessmentService, Depends(get_assessment_service)],
) -> QuestionAdminView:
    return await service.add_question(
        assessment_id=assessment_id,
        payload=payload,
        user_id=UUID(current_user.user_id),
    )


@router.patch(
    "/{assessment_id}/questions/{question_id}",
    response_model=QuestionAdminView,
    summary="Update a question in a draft assessment",
)
async def update_question(
    assessment_id: UUID,
    question_id: UUID,
    payload: QuestionUpdate,
    current_user: Annotated[UserContext, Depends(require_role("OFFICER", "ADMIN"))],
    service: Annotated[AssessmentService, Depends(get_assessment_service)],
) -> QuestionAdminView:
    return await service.update_question(
        assessment_id=assessment_id,
        question_id=question_id,
        payload=payload,
        user_id=UUID(current_user.user_id),
    )


@router.delete(
    "/{assessment_id}/questions/{question_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a question from a draft assessment",
)
async def delete_question(
    assessment_id: UUID,
    question_id: UUID,
    current_user: Annotated[UserContext, Depends(require_role("OFFICER", "ADMIN"))],
    service: Annotated[AssessmentService, Depends(get_assessment_service)],
) -> None:
    await service.delete_question(
        assessment_id=assessment_id,
        question_id=question_id,
        user_id=UUID(current_user.user_id),
    )


@router.post(
    "/{assessment_id}/publish",
    response_model=AssessmentSummary,
    summary="Publish assessment (Validates questions & marks)",
)
async def publish_assessment(
    assessment_id: UUID,
    current_user: Annotated[UserContext, Depends(require_role("OFFICER", "ADMIN"))],
    service: Annotated[AssessmentService, Depends(get_assessment_service)],
) -> AssessmentSummary:
    return await service.publish_assessment(
        assessment_id=assessment_id, user_id=UUID(current_user.user_id)
    )


@router.post(
    "/{assessment_id}/archive",
    response_model=AssessmentSummary,
    summary="Archive an assessment",
)
async def archive_assessment(
    assessment_id: UUID,
    current_user: Annotated[UserContext, Depends(require_role("OFFICER", "ADMIN"))],
    service: Annotated[AssessmentService, Depends(get_assessment_service)],
) -> AssessmentSummary:
    return await service.archive_assessment(
        assessment_id=assessment_id, user_id=UUID(current_user.user_id)
    )


@router.post(
    "/{assessment_id}/assign",
    response_model=list[AssessmentAssignmentResponse],
    summary="Assign assessment to students",
)
async def assign_assessment(
    assessment_id: UUID,
    payload: AssessmentAssignRequest,
    current_user: Annotated[UserContext, Depends(require_role("OFFICER", "ADMIN"))],
    service: Annotated[AssessmentService, Depends(get_assessment_service)],
) -> list[AssessmentAssignmentResponse]:
    return await service.assign_assessment(
        assessment_id=assessment_id,
        payload=payload,
        assigned_by_user_id=UUID(current_user.user_id),
    )


@router.get(
    "/{assessment_id}/results",
    response_model=OfficerAssessmentResultsView,
    summary="View assessment results summary (Officer/Admin)",
)
async def get_assessment_results_officer(
    assessment_id: UUID,
    current_user: Annotated[UserContext, Depends(require_role("OFFICER", "ADMIN"))],
    service: Annotated[AssessmentService, Depends(get_assessment_service)],
) -> OfficerAssessmentResultsView:
    return await service.get_assessment_results_for_officer(assessment_id=assessment_id)


# ---------------------------------------------------------------------------
# Student Assessment Preview & Test Start
# ---------------------------------------------------------------------------

@router.get(
    "/{assessment_id}/preview",
    response_model=AssessmentStudentPreview,
    summary="Student pre-test preview (No answers)",
)
async def get_assessment_student_preview(
    assessment_id: UUID,
    current_user: Annotated[UserContext, Depends(require_role("STUDENT"))],
    service: Annotated[AssessmentService, Depends(get_assessment_service)],
) -> AssessmentStudentPreview:
    return await service.get_student_assessment_preview(
        assessment_id=assessment_id,
        student_user_id=UUID(current_user.user_id),
    )


@router.post(
    "/{assessment_id}/start",
    response_model=StartAttemptResponse,
    summary="Start or resume a timed assessment attempt",
)
async def start_assessment(
    assessment_id: UUID,
    current_user: Annotated[UserContext, Depends(require_role("STUDENT"))],
    service: Annotated[AssessmentService, Depends(get_assessment_service)],
) -> StartAttemptResponse:
    return await service.start_assessment_attempt(
        assessment_id=assessment_id,
        student_user_id=UUID(current_user.user_id),
    )
