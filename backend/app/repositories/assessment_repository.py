"""
Assessment Repository.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Sequence
from uuid import UUID

from sqlalchemy import desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.models.assessment import (
    Assessment,
    AssessmentAssignment,
    AssessmentAttempt,
    AssessmentQuestion,
    AssessmentResponse,
    AssessmentResult,
)
from app.models.preparation import PreparationCategory, PreparationRole, PreparationTopic
from app.models.placement_drive import PlacementDrive
from app.models.student_profile import StudentProfile
from app.models.user import User


class AssessmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # -----------------------------------------------------------------------
    # Assessments
    # -----------------------------------------------------------------------

    async def create_assessment(self, assessment: Assessment) -> Assessment:
        self.session.add(assessment)
        await self.session.flush()
        await self.session.refresh(assessment)
        return assessment

    async def get_assessment_by_id(
        self,
        assessment_id: UUID,
        load_questions: bool = True,
        load_relations: bool = True,
    ) -> Assessment | None:
        stmt = select(Assessment).where(Assessment.id == assessment_id)
        if load_relations:
            stmt = stmt.options(
                selectinload(Assessment.category),
                selectinload(Assessment.topic),
                selectinload(Assessment.role),
                selectinload(Assessment.placement_drive),
                selectinload(Assessment.created_by),
            )
        if load_questions:
            stmt = stmt.options(
                selectinload(Assessment.questions).selectinload(AssessmentQuestion.topic)
            )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_assessments(
        self,
        status: str | None = None,
        category_id: UUID | None = None,
        topic_id: UUID | None = None,
        role_id: UUID | None = None,
        placement_drive_id: UUID | None = None,
        difficulty: str | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[Sequence[Assessment], int]:
        stmt = (
            select(Assessment)
            .options(
                selectinload(Assessment.category),
                selectinload(Assessment.topic),
                selectinload(Assessment.role),
                selectinload(Assessment.placement_drive),
                selectinload(Assessment.questions),
            )
        )

        if status:
            stmt = stmt.where(Assessment.status == status)
        if category_id:
            stmt = stmt.where(Assessment.category_id == category_id)
        if topic_id:
            stmt = stmt.where(Assessment.topic_id == topic_id)
        if role_id:
            stmt = stmt.where(Assessment.role_id == role_id)
        if placement_drive_id:
            stmt = stmt.where(Assessment.placement_drive_id == placement_drive_id)
        if difficulty:
            stmt = stmt.where(Assessment.difficulty == difficulty)
        if search:
            stmt = stmt.where(
                Assessment.title.ilike(f"%{search}%")
                | Assessment.description.ilike(f"%{search}%")
            )

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.session.execute(count_stmt)).scalar() or 0

        stmt = (
            stmt.order_by(Assessment.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all(), total

    async def update_assessment(self, assessment: Assessment) -> Assessment:
        await self.session.flush()
        await self.session.refresh(assessment)
        return assessment

    # -----------------------------------------------------------------------
    # Questions
    # -----------------------------------------------------------------------

    async def create_question(self, question: AssessmentQuestion) -> AssessmentQuestion:
        self.session.add(question)
        await self.session.flush()
        await self.session.refresh(question)
        return question

    async def get_question_by_id(self, question_id: UUID) -> AssessmentQuestion | None:
        stmt = (
            select(AssessmentQuestion)
            .where(AssessmentQuestion.id == question_id)
            .options(selectinload(AssessmentQuestion.topic))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_questions_for_assessment(
        self, assessment_id: UUID
    ) -> Sequence[AssessmentQuestion]:
        stmt = (
            select(AssessmentQuestion)
            .where(AssessmentQuestion.assessment_id == assessment_id)
            .order_by(AssessmentQuestion.sequence_order, AssessmentQuestion.created_at)
            .options(selectinload(AssessmentQuestion.topic))
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_question(self, question: AssessmentQuestion) -> AssessmentQuestion:
        await self.session.flush()
        await self.session.refresh(question)
        return question

    async def delete_question(self, question: AssessmentQuestion) -> None:
        await self.session.delete(question)
        await self.session.flush()

    async def recalculate_total_marks(self, assessment_id: UUID) -> Decimal:
        stmt = select(func.coalesce(func.sum(AssessmentQuestion.marks), 0)).where(
            AssessmentQuestion.assessment_id == assessment_id
        )
        total = (await self.session.execute(stmt)).scalar()
        total_decimal = Decimal(str(total or "0.00"))

        update_stmt = (
            update(Assessment)
            .where(Assessment.id == assessment_id)
            .values(total_marks=total_decimal)
        )
        await self.session.execute(update_stmt)
        await self.session.flush()
        return total_decimal

    # -----------------------------------------------------------------------
    # Assignments
    # -----------------------------------------------------------------------

    async def create_assignments(
        self, assignments: list[AssessmentAssignment]
    ) -> Sequence[AssessmentAssignment]:
        self.session.add_all(assignments)
        await self.session.flush()
        return assignments

    async def get_assignment(
        self, assessment_id: UUID, student_user_id: UUID
    ) -> AssessmentAssignment | None:
        stmt = (
            select(AssessmentAssignment)
            .where(
                AssessmentAssignment.assessment_id == assessment_id,
                AssessmentAssignment.student_user_id == student_user_id,
            )
            .options(
                selectinload(AssessmentAssignment.assessment).selectinload(Assessment.questions),
                selectinload(AssessmentAssignment.student),
                selectinload(AssessmentAssignment.attempts).selectinload(AssessmentAttempt.result),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_assignment_by_id(self, assignment_id: UUID) -> AssessmentAssignment | None:
        stmt = (
            select(AssessmentAssignment)
            .where(AssessmentAssignment.id == assignment_id)
            .options(
                selectinload(AssessmentAssignment.assessment).selectinload(Assessment.questions),
                selectinload(AssessmentAssignment.student),
                selectinload(AssessmentAssignment.attempts).selectinload(AssessmentAttempt.result),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_student_assignments(
        self, student_user_id: UUID, status: str | None = None
    ) -> Sequence[AssessmentAssignment]:
        stmt = (
            select(AssessmentAssignment)
            .where(AssessmentAssignment.student_user_id == student_user_id)
            .join(AssessmentAssignment.assessment)
            .options(
                selectinload(AssessmentAssignment.student),
                selectinload(AssessmentAssignment.assessment).selectinload(Assessment.category),
                selectinload(AssessmentAssignment.assessment).selectinload(Assessment.topic),
                selectinload(AssessmentAssignment.assessment).selectinload(Assessment.role),
                selectinload(AssessmentAssignment.assessment).selectinload(Assessment.placement_drive),
                selectinload(AssessmentAssignment.assessment).selectinload(Assessment.questions),
                selectinload(AssessmentAssignment.attempts).selectinload(AssessmentAttempt.result),
            )
            .order_by(AssessmentAssignment.created_at.desc())
        )

        if status:
            stmt = stmt.where(AssessmentAssignment.status == status)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def list_assessment_assignments(
        self, assessment_id: UUID
    ) -> Sequence[AssessmentAssignment]:
        stmt = (
            select(AssessmentAssignment)
            .where(AssessmentAssignment.assessment_id == assessment_id)
            .options(
                selectinload(AssessmentAssignment.student),
                selectinload(AssessmentAssignment.attempts).selectinload(AssessmentAttempt.result),
            )
            .order_by(AssessmentAssignment.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    # -----------------------------------------------------------------------
    # Attempts
    # -----------------------------------------------------------------------

    async def create_attempt(self, attempt: AssessmentAttempt) -> AssessmentAttempt:
        self.session.add(attempt)
        await self.session.flush()
        await self.session.refresh(attempt)
        return attempt

    async def get_attempt_by_id(
        self, attempt_id: UUID, load_relations: bool = True
    ) -> AssessmentAttempt | None:
        stmt = select(AssessmentAttempt).where(AssessmentAttempt.id == attempt_id)
        if load_relations:
            stmt = stmt.options(
                selectinload(AssessmentAttempt.assignment)
                .selectinload(AssessmentAssignment.assessment)
                .selectinload(Assessment.questions)
                .selectinload(AssessmentQuestion.topic),
                selectinload(AssessmentAttempt.assignment).selectinload(AssessmentAssignment.student),
                selectinload(AssessmentAttempt.responses).selectinload(AssessmentResponse.question),
                selectinload(AssessmentAttempt.result),
            )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_attempt_for_assignment(
        self, assignment_id: UUID
    ) -> AssessmentAttempt | None:
        stmt = (
            select(AssessmentAttempt)
            .where(
                AssessmentAttempt.assignment_id == assignment_id,
                AssessmentAttempt.status == "IN_PROGRESS",
            )
            .options(
                selectinload(AssessmentAttempt.responses),
                selectinload(AssessmentAttempt.assignment)
                .selectinload(AssessmentAssignment.assessment)
                .selectinload(Assessment.questions)
                .selectinload(AssessmentQuestion.topic),
            )
            .order_by(AssessmentAttempt.attempt_number.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


    # -----------------------------------------------------------------------
    # Responses
    # -----------------------------------------------------------------------

    async def upsert_response(
        self, attempt_id: UUID, question_id: UUID, selected_option: str | None
    ) -> AssessmentResponse:
        stmt = select(AssessmentResponse).where(
            AssessmentResponse.attempt_id == attempt_id,
            AssessmentResponse.question_id == question_id,
        )
        existing = (await self.session.execute(stmt)).scalar_one_or_none()

        now = datetime.now(timezone.utc)
        if existing:
            existing.selected_option = selected_option
            existing.answered_at = now
            await self.session.flush()
            return existing
        else:
            new_resp = AssessmentResponse(
                attempt_id=attempt_id,
                question_id=question_id,
                selected_option=selected_option,
                answered_at=now,
            )
            self.session.add(new_resp)
            await self.session.flush()
            return new_resp

    async def get_responses_for_attempt(
        self, attempt_id: UUID
    ) -> Sequence[AssessmentResponse]:
        stmt = (
            select(AssessmentResponse)
            .where(AssessmentResponse.attempt_id == attempt_id)
            .options(selectinload(AssessmentResponse.question))
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    # -----------------------------------------------------------------------
    # Results
    # -----------------------------------------------------------------------

    async def create_result(self, result: AssessmentResult) -> AssessmentResult:
        self.session.add(result)
        await self.session.flush()
        await self.session.refresh(result)
        return result

    async def get_result_by_attempt_id(
        self, attempt_id: UUID
    ) -> AssessmentResult | None:
        stmt = (
            select(AssessmentResult)
            .where(AssessmentResult.attempt_id == attempt_id)
            .options(
                selectinload(AssessmentResult.attempt)
                .selectinload(AssessmentAttempt.assignment)
                .selectinload(AssessmentAssignment.assessment)
                .selectinload(Assessment.questions)
                .selectinload(AssessmentQuestion.topic),
                selectinload(AssessmentResult.attempt)
                .selectinload(AssessmentAttempt.responses)
                .selectinload(AssessmentResponse.question),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_student_history(
        self, student_user_id: UUID
    ) -> Sequence[AssessmentResult]:
        stmt = (
            select(AssessmentResult)
            .join(AssessmentResult.attempt)
            .join(AssessmentAttempt.assignment)
            .where(AssessmentAssignment.student_user_id == student_user_id)
            .options(
                selectinload(AssessmentResult.attempt)
                .selectinload(AssessmentAttempt.assignment)
                .selectinload(AssessmentAssignment.assessment)
            )
            .order_by(AssessmentResult.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
