"""
CampusFlow — AI Voice Agent Mock Interview API Endpoints.
"""
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import UserContext, get_db, require_role
from app.core.rag.models import (
    GroundedEvaluation,
    RAGDocument,
    RAGQueryRequest,
    RAGQueryResponse,
)
from app.repositories.mock_interview_repository import MockInterviewRepository
from app.schemas.mock_interview import (
    MockInterviewEvaluateRequest,
    MockInterviewEvaluationItem,
    MockInterviewSessionCreate,
    MockInterviewSessionResponse,
)
from app.services.mock_interview_service import MockInterviewService

router = APIRouter()


def get_mock_interview_service(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> MockInterviewService:
    repo = MockInterviewRepository(session)
    return MockInterviewService(repo)


@router.post(
    "/sessions",
    response_model=MockInterviewSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_mock_interview_session(
    data: MockInterviewSessionCreate,
    current_user: Annotated[UserContext, Depends(require_role("STUDENT", "OFFICER", "ADMIN"))],
    service: Annotated[MockInterviewService, Depends(get_mock_interview_service)],
) -> MockInterviewSessionResponse:
    """Create a new voice agent mock interview session for the current student."""
    session = await service.create_session(user_id=UUID(current_user.user_id), data=data)
    return session


@router.post(
    "/sessions/{session_id}/evaluate-answer",
    response_model=MockInterviewEvaluationItem,
)
async def evaluate_mock_interview_answer(
    session_id: UUID,
    request: MockInterviewEvaluateRequest,
    current_user: Annotated[UserContext, Depends(require_role("STUDENT", "OFFICER", "ADMIN"))],
    service: Annotated[MockInterviewService, Depends(get_mock_interview_service)],
) -> MockInterviewEvaluationItem:
    """Evaluate a spoken/transcribed answer across technical, communication, and structural dimensions."""
    evaluation = await service.evaluate_answer(
        session_id=session_id,
        user_id=UUID(current_user.user_id),
        request=request,
    )
    return evaluation


@router.post(
    "/sessions/{session_id}/complete",
    response_model=MockInterviewSessionResponse,
)
async def complete_mock_interview_session(
    session_id: UUID,
    current_user: Annotated[UserContext, Depends(require_role("STUDENT", "OFFICER", "ADMIN"))],
    service: Annotated[MockInterviewService, Depends(get_mock_interview_service)],
) -> MockInterviewSessionResponse:
    """Finalize the mock interview session and generate the comprehensive performance report."""
    session = await service.complete_session(session_id=session_id, user_id=UUID(current_user.user_id))
    return session


@router.get(
    "/sessions",
    response_model=list[MockInterviewSessionResponse],
)
async def list_user_mock_interview_sessions(
    current_user: Annotated[UserContext, Depends(require_role("STUDENT", "OFFICER", "ADMIN"))],
    service: Annotated[MockInterviewService, Depends(get_mock_interview_service)],
) -> list[MockInterviewSessionResponse]:
    """List all past mock interview sessions for the current student."""
    sessions = await service.list_user_sessions(user_id=UUID(current_user.user_id))
    return list(sessions)


@router.get(
    "/sessions/{session_id}",
    response_model=MockInterviewSessionResponse,
)
async def get_mock_interview_session_details(
    session_id: UUID,
    current_user: Annotated[UserContext, Depends(require_role("STUDENT", "OFFICER", "ADMIN"))],
    service: Annotated[MockInterviewService, Depends(get_mock_interview_service)],
) -> MockInterviewSessionResponse:
    """Retrieve full details, evaluations, and performance report for a mock interview session."""
    session = await service.get_session_details(session_id=session_id, user_id=UUID(current_user.user_id))
    return session


@router.get(
    "/tracks/{track_id}/rag-questions",
    response_model=list[RAGDocument],
)
async def get_track_rag_questions(
    track_id: str,
    count: int = 5,
    offset: int = 0,
    service: Annotated[MockInterviewService, Depends(get_mock_interview_service)] = None,
) -> list[RAGDocument]:
    """Retrieve 5 dynamic questions curated directly from the 7 verified handbook PDF indexes."""
    return service.get_track_questions(track_id=track_id, count=count, offset=offset)


@router.post(
    "/rag/query",
    response_model=RAGQueryResponse,
)
async def query_rag_knowledge(
    request: RAGQueryRequest,
    service: Annotated[MockInterviewService, Depends(get_mock_interview_service)] = None,
) -> RAGQueryResponse:
    """Perform hybrid retrieval across the 996+ interview handbook passages."""
    return service.search_rag(query=request.query, track_id=request.track_id, top_k=request.top_k)
