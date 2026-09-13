"""
Assessment Service.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import logging
from typing import Any, Sequence
from uuid import UUID

from fastapi import HTTPException, status

from app.models.assessment import (
    Assessment,
    AssessmentAssignment,
    AssessmentAttempt,
    AssessmentQuestion,
    AssessmentResponse,
    AssessmentResult,
)
from app.models.audit_log import AuditLog
from app.models.user import User
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
    OptionItem,
    QuestionAdminView,
    QuestionAnswerItem,
    QuestionCreate,
    QuestionReviewView,
    QuestionStudentView,
    QuestionUpdate,
    SaveProgressRequest,
    StartAttemptResponse,
    SubmitAttemptRequest,
)
from app.services.notification_dispatcher import NotificationDispatcher

logger = logging.getLogger(__name__)


class AssessmentService:
    def __init__(
        self,
        assessment_repo: AssessmentRepository,
        audit_repo: AuditLogRepository,
        dispatcher: NotificationDispatcher | None = None,
    ) -> None:
        self.assessment_repo = assessment_repo
        self.audit_repo = audit_repo
        self.dispatcher = dispatcher

    def _log_audit(
        self,
        user_id: UUID,
        action: str,
        entity_id: UUID,
        old_state: dict | None = None,
        new_state: dict | None = None,
    ) -> None:
        audit_log = AuditLog(
            performed_by_user_id=user_id,
            action=action,
            entity_type="ASSESSMENT",
            entity_id=entity_id,
            old_state=old_state,
            new_state=new_state,
        )
        self.audit_repo.add(audit_log)

    # -----------------------------------------------------------------------
    # Officer Assessment Lifecycle
    # -----------------------------------------------------------------------

    async def create_assessment(
        self, payload: AssessmentCreate, user_id: UUID
    ) -> AssessmentSummary:
        assessment = Assessment(
            title=payload.title,
            description=payload.description,
            category_id=payload.category_id,
            topic_id=payload.topic_id,
            role_id=payload.role_id,
            placement_drive_id=payload.placement_drive_id,
            difficulty=payload.difficulty,
            duration_minutes=payload.duration_minutes,
            total_marks=Decimal("0.00"),
            pass_percentage=payload.pass_percentage,
            status="DRAFT",
            allow_multiple_attempts=payload.allow_multiple_attempts,
            created_by_user_id=user_id,
        )
        created = await self.assessment_repo.create_assessment(assessment)

        self._log_audit(
            user_id=user_id,
            action="ASSESSMENT_CREATED",
            entity_id=created.id,
            new_state={
                "title": created.title,
                "difficulty": created.difficulty,
                "duration_minutes": created.duration_minutes,
            },
        )
        await self.assessment_repo.session.commit()

        loaded = await self.assessment_repo.get_assessment_by_id(created.id)
        return self._to_summary(loaded)

    async def update_assessment(
        self, assessment_id: UUID, payload: AssessmentUpdate, user_id: UUID
    ) -> AssessmentSummary:
        assessment = await self.assessment_repo.get_assessment_by_id(assessment_id)
        if not assessment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assessment not found.",
            )

        if assessment.status != "DRAFT":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot modify assessment details unless it is in DRAFT status.",
            )

        old_state = {"title": assessment.title, "duration_minutes": assessment.duration_minutes}

        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(assessment, field, value)

        await self.assessment_repo.update_assessment(assessment)

        self._log_audit(
            user_id=user_id,
            action="ASSESSMENT_UPDATED",
            entity_id=assessment.id,
            old_state=old_state,
            new_state={"title": assessment.title, "duration_minutes": assessment.duration_minutes},
        )
        await self.assessment_repo.session.commit()

        loaded = await self.assessment_repo.get_assessment_by_id(assessment.id)
        return self._to_summary(loaded)

    async def get_assessment_admin(self, assessment_id: UUID) -> AssessmentAdminDetail:
        assessment = await self.assessment_repo.get_assessment_by_id(
            assessment_id, load_questions=True, load_relations=True
        )
        if not assessment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assessment not found.",
            )

        questions = [
            QuestionAdminView(
                id=q.id,
                assessment_id=q.assessment_id,
                topic_id=q.topic_id,
                topic_name=q.topic.name if q.topic else None,
                question_text=q.question_text,
                options=[OptionItem(**opt) for opt in q.options],
                correct_option=q.correct_option,
                explanation=q.explanation,
                marks=q.marks,
                sequence_order=q.sequence_order,
                created_at=q.created_at,
                updated_at=q.updated_at,
            )
            for q in assessment.questions
        ]

        assignments = await self.assessment_repo.list_assessment_assignments(assessment_id)
        assignments_count = len(assignments)
        completed_count = sum(1 for a in assignments if a.status == "COMPLETED")

        return AssessmentAdminDetail(
            id=assessment.id,
            title=assessment.title,
            description=assessment.description,
            category_id=assessment.category_id,
            category_name=assessment.category.name if assessment.category else None,
            topic_id=assessment.topic_id,
            topic_name=assessment.topic.name if assessment.topic else None,
            role_id=assessment.role_id,
            role_name=assessment.role.name if assessment.role else None,
            placement_drive_id=assessment.placement_drive_id,
            placement_drive_title=assessment.placement_drive.title if assessment.placement_drive else None,
            difficulty=assessment.difficulty,
            duration_minutes=assessment.duration_minutes,
            total_marks=assessment.total_marks,
            pass_percentage=assessment.pass_percentage,
            status=assessment.status,
            allow_multiple_attempts=assessment.allow_multiple_attempts,
            created_by_user_id=assessment.created_by_user_id,
            created_at=assessment.created_at,
            updated_at=assessment.updated_at,
            questions=questions,
            assignments_count=assignments_count,
            completed_count=completed_count,
        )

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
    ) -> tuple[list[AssessmentSummary], int]:
        assessments, total = await self.assessment_repo.list_assessments(
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
        return [self._to_summary(a) for a in assessments], total

    # -----------------------------------------------------------------------
    # Question Management (Draft Only)
    # -----------------------------------------------------------------------

    async def add_question(
        self, assessment_id: UUID, payload: QuestionCreate, user_id: UUID
    ) -> QuestionAdminView:
        assessment = await self.assessment_repo.get_assessment_by_id(assessment_id)
        if not assessment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assessment not found.",
            )

        if assessment.status != "DRAFT":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Questions can only be added to assessments in DRAFT status.",
            )

        options_dicts = [opt.model_dump() for opt in payload.options]
        question = AssessmentQuestion(
            assessment_id=assessment_id,
            topic_id=payload.topic_id or assessment.topic_id,
            question_text=payload.question_text,
            options=options_dicts,
            correct_option=payload.correct_option.strip().upper(),
            explanation=payload.explanation,
            marks=payload.marks,
            sequence_order=payload.sequence_order,
        )

        created = await self.assessment_repo.create_question(question)
        await self.assessment_repo.recalculate_total_marks(assessment_id)
        await self.assessment_repo.session.commit()

        loaded_q = await self.assessment_repo.get_question_by_id(created.id)
        return QuestionAdminView(
            id=loaded_q.id,
            assessment_id=loaded_q.assessment_id,
            topic_id=loaded_q.topic_id,
            topic_name=loaded_q.topic.name if loaded_q.topic else None,
            question_text=loaded_q.question_text,
            options=[OptionItem(**opt) for opt in loaded_q.options],
            correct_option=loaded_q.correct_option,
            explanation=loaded_q.explanation,
            marks=loaded_q.marks,
            sequence_order=loaded_q.sequence_order,
            created_at=loaded_q.created_at,
            updated_at=loaded_q.updated_at,
        )

    async def update_question(
        self,
        assessment_id: UUID,
        question_id: UUID,
        payload: QuestionUpdate,
        user_id: UUID,
    ) -> QuestionAdminView:
        assessment = await self.assessment_repo.get_assessment_by_id(assessment_id)
        if not assessment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assessment not found.",
            )

        if assessment.status != "DRAFT":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Questions can only be modified in DRAFT status.",
            )

        question = await self.assessment_repo.get_question_by_id(question_id)
        if not question or question.assessment_id != assessment_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found for this assessment.",
            )

        if payload.question_text is not None:
            question.question_text = payload.question_text
        if payload.options is not None:
            question.options = [opt.model_dump() for opt in payload.options]
        if payload.correct_option is not None:
            corr = payload.correct_option.strip().upper()
            opts = [opt["key"].strip().upper() for opt in question.options]
            if corr not in opts:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Correct option '{corr}' must match one of the option keys: {opts}",
                )
            question.correct_option = corr
        if payload.explanation is not None:
            question.explanation = payload.explanation
        if payload.marks is not None:
            question.marks = payload.marks
        if payload.topic_id is not None:
            question.topic_id = payload.topic_id
        if payload.sequence_order is not None:
            question.sequence_order = payload.sequence_order

        await self.assessment_repo.update_question(question)
        await self.assessment_repo.recalculate_total_marks(assessment_id)
        await self.assessment_repo.session.commit()

        loaded_q = await self.assessment_repo.get_question_by_id(question_id)
        return QuestionAdminView(
            id=loaded_q.id,
            assessment_id=loaded_q.assessment_id,
            topic_id=loaded_q.topic_id,
            topic_name=loaded_q.topic.name if loaded_q.topic else None,
            question_text=loaded_q.question_text,
            options=[OptionItem(**opt) for opt in loaded_q.options],
            correct_option=loaded_q.correct_option,
            explanation=loaded_q.explanation,
            marks=loaded_q.marks,
            sequence_order=loaded_q.sequence_order,
            created_at=loaded_q.created_at,
            updated_at=loaded_q.updated_at,
        )

    async def delete_question(
        self, assessment_id: UUID, question_id: UUID, user_id: UUID
    ) -> None:
        assessment = await self.assessment_repo.get_assessment_by_id(assessment_id)
        if not assessment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assessment not found.",
            )

        if assessment.status != "DRAFT":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Questions can only be removed from assessments in DRAFT status.",
            )

        question = await self.assessment_repo.get_question_by_id(question_id)
        if not question or question.assessment_id != assessment_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found for this assessment.",
            )

        await self.assessment_repo.delete_question(question)
        await self.assessment_repo.recalculate_total_marks(assessment_id)
        await self.assessment_repo.session.commit()

    # -----------------------------------------------------------------------
    # Publishing & Archiving
    # -----------------------------------------------------------------------

    async def publish_assessment(
        self, assessment_id: UUID, user_id: UUID
    ) -> AssessmentSummary:
        assessment = await self.assessment_repo.get_assessment_by_id(
            assessment_id, load_questions=True
        )
        if not assessment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assessment not found.",
            )

        if assessment.status != "DRAFT":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Assessment cannot be published from status '{assessment.status}'.",
            )

        if not assessment.questions:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Cannot publish an assessment with zero questions. Add at least one MCQ.",
            )

        # Recalculate total marks authoritatively
        total_marks = sum(Decimal(str(q.marks)) for q in assessment.questions)
        if total_marks <= Decimal("0.00"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Assessment must have positive total marks (> 0).",
            )

        # Validate question integrity
        for q in assessment.questions:
            if len(q.options) < 2:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Question '{q.question_text[:30]}' has fewer than 2 options.",
                )
            opt_keys = {opt["key"].strip().upper() for opt in q.options}
            if q.correct_option.strip().upper() not in opt_keys:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Question '{q.question_text[:30]}' has invalid correct option.",
                )

        assessment.total_marks = total_marks
        assessment.status = "PUBLISHED"
        await self.assessment_repo.update_assessment(assessment)

        self._log_audit(
            user_id=user_id,
            action="ASSESSMENT_PUBLISHED",
            entity_id=assessment.id,
            new_state={
                "status": "PUBLISHED",
                "questions_count": len(assessment.questions),
                "total_marks": float(total_marks),
            },
        )
        await self.assessment_repo.session.commit()

        loaded = await self.assessment_repo.get_assessment_by_id(assessment.id)
        return self._to_summary(loaded)

    async def archive_assessment(
        self, assessment_id: UUID, user_id: UUID
    ) -> AssessmentSummary:
        assessment = await self.assessment_repo.get_assessment_by_id(assessment_id)
        if not assessment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assessment not found.",
            )

        assessment.status = "ARCHIVED"
        await self.assessment_repo.update_assessment(assessment)

        self._log_audit(
            user_id=user_id,
            action="ASSESSMENT_ARCHIVED",
            entity_id=assessment.id,
            new_state={"status": "ARCHIVED"},
        )
        await self.assessment_repo.session.commit()

        loaded = await self.assessment_repo.get_assessment_by_id(assessment.id)
        return self._to_summary(loaded)

    # -----------------------------------------------------------------------
    # Assignment
    # -----------------------------------------------------------------------

    async def assign_assessment(
        self, assessment_id: UUID, payload: AssessmentAssignRequest, assigned_by_user_id: UUID
    ) -> list[AssessmentAssignmentResponse]:
        assessment = await self.assessment_repo.get_assessment_by_id(assessment_id)
        if not assessment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assessment not found.",
            )

        if assessment.status != "PUBLISHED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PUBLISHED assessments can be assigned to students.",
            )

        created_assignments: list[AssessmentAssignment] = []
        notif_recipients: list[UUID] = []

        for student_id in payload.student_user_ids:
            existing = await self.assessment_repo.get_assignment(assessment_id, student_id)
            if not existing:
                assignment = AssessmentAssignment(
                    assessment_id=assessment_id,
                    student_user_id=student_id,
                    assigned_by_user_id=assigned_by_user_id,
                    due_date=payload.due_date,
                    status="ASSIGNED",
                )
                self.assessment_repo.session.add(assignment)
                created_assignments.append(assignment)
                notif_recipients.append(student_id)

        self._log_audit(
            user_id=assigned_by_user_id,
            action="ASSESSMENT_ASSIGNED",
            entity_id=assessment.id,
            new_state={
                "assigned_count": len(created_assignments),
                "total_requested": len(payload.student_user_ids),
                "due_date": payload.due_date.isoformat() if payload.due_date else None,
            },
        )
        await self.assessment_repo.session.commit()

        # Post-commit notification dispatch
        if notif_recipients and self.dispatcher:
            try:
                items = [
                    {
                        "user_id": uid,
                        "title": f"New Practice Assessment: {assessment.title}",
                        "body": f"You have been assigned the practice assessment '{assessment.title}'. Duration: {assessment.duration_minutes} mins.",
                        "notification_type": "ASSESSMENT_ASSIGNED",
                        "reference_id": assessment.id,
                        "reference_type": "ASSESSMENT",
                        "send_push": True,
                    }
                    for uid in notif_recipients
                ]
                await self.dispatcher.dispatch_bulk_notifications(items)
            except Exception as e:
                logger.error(
                    "Failed to dispatch assessment assignment notifications: %s", e
                )

        assignments = await self.assessment_repo.list_assessment_assignments(assessment_id)
        return [self._to_assignment_response(a) for a in assignments]

    async def get_assessment_results_for_officer(
        self, assessment_id: UUID
    ) -> OfficerAssessmentResultsView:
        assessment = await self.assessment_repo.get_assessment_by_id(assessment_id)
        if not assessment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assessment not found.",
            )

        assignments = await self.assessment_repo.list_assessment_assignments(assessment_id)
        results = [self._to_assignment_response(a) for a in assignments]

        total_assigned = len(assignments)
        total_started = sum(1 for a in assignments if a.status in ("IN_PROGRESS", "COMPLETED"))
        completed_assignments = [a for a in assignments if a.status == "COMPLETED"]
        total_completed = len(completed_assignments)

        scores = []
        percentages = []
        pass_count = 0

        for a in assignments:
            if a.attempts:
                latest_att = a.attempts[-1]
                if latest_att.result:
                    res = latest_att.result
                    scores.append(res.score_obtained)
                    percentages.append(res.percentage)
                    if res.is_passed:
                        pass_count += 1

        avg_score = (sum(scores) / len(scores)) if scores else None
        avg_pct = (sum(percentages) / len(percentages)) if percentages else None

        return OfficerAssessmentResultsView(
            assessment_id=assessment.id,
            assessment_title=assessment.title,
            total_assigned=total_assigned,
            total_started=total_started,
            total_completed=total_completed,
            average_score=Decimal(str(round(avg_score, 2))) if avg_score is not None else None,
            average_percentage=Decimal(str(round(avg_pct, 2))) if avg_pct is not None else None,
            pass_count=pass_count,
            results=results,
        )

    # -----------------------------------------------------------------------
    # Student Test Taking Engine
    # -----------------------------------------------------------------------

    async def get_student_assigned_assessments(
        self, student_user_id: UUID, status: str | None = None
    ) -> list[AssessmentAssignmentResponse]:
        assignments = await self.assessment_repo.list_student_assignments(
            student_user_id, status=status
        )
        return [self._to_assignment_response(a) for a in assignments]

    async def get_student_assessment_preview(
        self, assessment_id: UUID, student_user_id: UUID
    ) -> AssessmentStudentPreview:
        assignment = await self.assessment_repo.get_assignment(assessment_id, student_user_id)
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assessment assignment not found for this student.",
            )

        assessment = assignment.assessment
        if assessment.status != "PUBLISHED":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This assessment is currently unavailable.",
            )

        # Check if active attempt exists
        active_attempt = await self.assessment_repo.get_active_attempt_for_assignment(
            assignment.id
        )

        has_active = False
        active_id = None
        active_exp = None
        if active_attempt:
            now = datetime.now(timezone.utc)
            if now < active_attempt.expires_at:
                has_active = True
                active_id = active_attempt.id
                active_exp = active_attempt.expires_at

        # Check latest completed result
        latest_res = None
        if assignment.attempts:
            for att in reversed(assignment.attempts):
                if att.result:
                    latest_res = att.result
                    break

        return AssessmentStudentPreview(
            id=assessment.id,
            assignment_id=assignment.id,
            title=assessment.title,
            description=assessment.description,
            category_name=assessment.category.name if assessment.category else None,
            topic_name=assessment.topic.name if assessment.topic else None,
            role_name=assessment.role.name if assessment.role else None,
            placement_drive_title=assessment.placement_drive.title if assessment.placement_drive else None,
            difficulty=assessment.difficulty,
            duration_minutes=assessment.duration_minutes,
            question_count=len(assessment.questions),
            total_marks=assessment.total_marks,
            pass_percentage=assessment.pass_percentage,
            due_date=assignment.due_date,
            assignment_status=assignment.status,
            has_active_attempt=has_active,
            active_attempt_id=active_id,
            active_attempt_expires_at=active_exp,
            latest_result_id=latest_res.id if latest_res else None,
            latest_score=latest_res.score_obtained if latest_res else None,
            latest_percentage=latest_res.percentage if latest_res else None,
            latest_passed=latest_res.is_passed if latest_res else None,
        )

    async def start_assessment_attempt(
        self, assessment_id: UUID, student_user_id: UUID
    ) -> StartAttemptResponse:
        assignment = await self.assessment_repo.get_assignment(assessment_id, student_user_id)
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="You have not been assigned this assessment.",
            )

        assessment = assignment.assessment
        if assessment.status != "PUBLISHED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assessment is not currently active.",
            )

        now = datetime.now(timezone.utc)

        # Check for existing in-progress attempt
        active_attempt = await self.assessment_repo.get_active_attempt_for_assignment(
            assignment.id
        )

        if active_attempt:
            if now <= active_attempt.expires_at:
                # RESUME ACTIVE ATTEMPT
                saved_resps = {
                    str(r.question_id): r.selected_option
                    for r in active_attempt.responses
                }
                questions = [
                    QuestionStudentView(
                        id=q.id,
                        assessment_id=q.assessment_id,
                        topic_id=q.topic_id,
                        question_text=q.question_text,
                        options=[OptionItem(**opt) for opt in q.options],
                        marks=q.marks,
                        sequence_order=q.sequence_order,
                    )
                    for q in assessment.questions
                ]
                return StartAttemptResponse(
                    attempt_id=active_attempt.id,
                    assessment_id=assessment.id,
                    assignment_id=assignment.id,
                    title=assessment.title,
                    duration_minutes=assessment.duration_minutes,
                    started_at=active_attempt.started_at,
                    expires_at=active_attempt.expires_at,
                    questions=questions,
                    saved_responses=saved_resps,
                )
            else:
                # Expired while in progress -> auto finalize
                await self._evaluate_and_finalize_attempt(active_attempt, is_expired=True)

        # Check if already completed and multiple attempts not allowed
        if not assessment.allow_multiple_attempts:
            completed = any(att.status in ("SUBMITTED", "EXPIRED") for att in assignment.attempts)
            if completed:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="You have already completed this practice assessment.",
                )

        # CREATE NEW ATTEMPT
        attempt_number = len(assignment.attempts) + 1
        expires_at = now + timedelta(minutes=assessment.duration_minutes)

        new_attempt = AssessmentAttempt(
            assignment_id=assignment.id,
            attempt_number=attempt_number,
            status="IN_PROGRESS",
            started_at=now,
            expires_at=expires_at,
        )
        created_attempt = await self.assessment_repo.create_attempt(new_attempt)
        assignment.status = "IN_PROGRESS"
        await self.assessment_repo.session.commit()

        questions = [
            QuestionStudentView(
                id=q.id,
                assessment_id=q.assessment_id,
                topic_id=q.topic_id,
                question_text=q.question_text,
                options=[OptionItem(**opt) for opt in q.options],
                marks=q.marks,
                sequence_order=q.sequence_order,
            )
            for q in assessment.questions
        ]

        return StartAttemptResponse(
            attempt_id=created_attempt.id,
            assessment_id=assessment.id,
            assignment_id=assignment.id,
            title=assessment.title,
            duration_minutes=assessment.duration_minutes,
            started_at=created_attempt.started_at,
            expires_at=created_attempt.expires_at,
            questions=questions,
            saved_responses={},
        )

    async def get_active_attempt(
        self, attempt_id: UUID, student_user_id: UUID
    ) -> StartAttemptResponse:
        attempt = await self.assessment_repo.get_attempt_by_id(attempt_id)
        if not attempt or attempt.assignment.student_user_id != student_user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Active assessment attempt not found.",
            )

        if attempt.status != "IN_PROGRESS":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"This assessment attempt is already {attempt.status.lower()}.",
            )

        now = datetime.now(timezone.utc)
        if now > attempt.expires_at:
            await self._evaluate_and_finalize_attempt(attempt, is_expired=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assessment attempt has expired.",
            )

        assessment = attempt.assignment.assessment
        saved_resps = {
            str(r.question_id): r.selected_option
            for r in attempt.responses
        }
        questions = [
            QuestionStudentView(
                id=q.id,
                assessment_id=q.assessment_id,
                topic_id=q.topic_id,
                question_text=q.question_text,
                options=[OptionItem(**opt) for opt in q.options],
                marks=q.marks,
                sequence_order=q.sequence_order,
            )
            for q in assessment.questions
        ]

        return StartAttemptResponse(
            attempt_id=attempt.id,
            assessment_id=assessment.id,
            assignment_id=attempt.assignment_id,
            title=assessment.title,
            duration_minutes=assessment.duration_minutes,
            started_at=attempt.started_at,
            expires_at=attempt.expires_at,
            questions=questions,
            saved_responses=saved_resps,
        )

    async def save_progress(
        self, attempt_id: UUID, student_user_id: UUID, payload: SaveProgressRequest
    ) -> dict[str, Any]:
        attempt = await self.assessment_repo.get_attempt_by_id(attempt_id)
        if not attempt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assessment attempt not found.",
            )

        # IDOR protection
        if attempt.assignment.student_user_id != student_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this attempt.",
            )

        if attempt.status != "IN_PROGRESS":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Attempt is already {attempt.status}.",
            )

        # Server authoritative expiry check
        now = datetime.now(timezone.utc)
        if now > attempt.expires_at:
            await self._evaluate_and_finalize_attempt(attempt, is_expired=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assessment attempt has expired.",
            )

        valid_questions = {q.id: q for q in attempt.assignment.assessment.questions}

        saved_count = 0
        for item in payload.responses:
            if item.question_id not in valid_questions:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Question {item.question_id} does not belong to this assessment.",
                )
            
            if item.selected_option is not None:
                q = valid_questions[item.question_id]
                valid_keys = {opt["key"].strip().upper() for opt in q.options}
                if item.selected_option.strip().upper() not in valid_keys:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=f"Option {item.selected_option} is not a valid choice for question {item.question_id}.",
                    )

            await self.assessment_repo.upsert_response(
                attempt_id=attempt.id,
                question_id=item.question_id,
                selected_option=item.selected_option.strip().upper() if item.selected_option else None,
            )
            saved_count += 1

        await self.assessment_repo.session.commit()
        return {"status": "saved", "saved_count": saved_count}

    async def submit_assessment_attempt(
        self,
        attempt_id: UUID,
        student_user_id: UUID,
        payload: SubmitAttemptRequest | None = None,
    ) -> AssessmentResultResponse:
        attempt = await self.assessment_repo.get_attempt_by_id(attempt_id)
        if not attempt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assessment attempt not found.",
            )

        # IDOR protection
        if attempt.assignment.student_user_id != student_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to submit this attempt.",
            )

        # Idempotent return if already submitted
        if attempt.status in ("SUBMITTED", "EXPIRED"):
            existing_res = await self.assessment_repo.get_result_by_attempt_id(attempt.id)
            if existing_res:
                return self._to_result_response(existing_res)

        # Save any responses provided in submit request
        if payload and payload.responses:
            valid_questions = {q.id: q for q in attempt.assignment.assessment.questions}
            for item in payload.responses:
                if item.question_id in valid_questions:
                    selected = item.selected_option.strip().upper() if item.selected_option else None
                    if selected:
                        q = valid_questions[item.question_id]
                        valid_keys = {opt["key"].strip().upper() for opt in q.options}
                        if selected not in valid_keys:
                            continue
                    await self.assessment_repo.upsert_response(
                        attempt_id=attempt.id,
                        question_id=item.question_id,
                        selected_option=selected,
                    )

        # Authoritative scoring
        result = await self._evaluate_and_finalize_attempt(attempt, is_expired=False)
        self._log_audit(
            user_id=student_user_id,
            action="ASSESSMENT_SUBMITTED",
            entity_id=attempt.id,
            new_state={
                "score_obtained": float(result.score_obtained),
                "total_score": float(result.total_score),
                "percentage": float(result.percentage),
                "is_passed": result.is_passed,
            },
        )
        await self.assessment_repo.session.commit()

        loaded_res = await self.assessment_repo.get_result_by_attempt_id(attempt.id)
        return self._to_result_response(loaded_res)

    async def get_attempt_result(
        self, attempt_id: UUID, current_user_id: UUID, current_user_role: str
    ) -> AssessmentResultResponse:
        result = await self.assessment_repo.get_result_by_attempt_id(attempt_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assessment result not found.",
            )

        # RBAC & IDOR check
        student_id = result.attempt.assignment.student_user_id
        if current_user_role == "STUDENT" and student_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view this assessment result.",
            )

        return self._to_result_response(result)

    async def get_student_history(
        self, student_user_id: UUID
    ) -> list[AssessmentResultResponse]:
        results = await self.assessment_repo.list_student_history(student_user_id)
        return [self._to_result_response(r, include_review=False) for r in results]

    # -----------------------------------------------------------------------
    # Authoritative Evaluation Engine
    # -----------------------------------------------------------------------

    async def _evaluate_and_finalize_attempt(
        self, attempt: AssessmentAttempt, is_expired: bool = False
    ) -> AssessmentResult:
        # Check if result already exists to prevent duplicate result creation
        existing_result = await self.assessment_repo.get_result_by_attempt_id(attempt.id)
        if existing_result:
            return existing_result

        now = datetime.now(timezone.utc)
        assessment = attempt.assignment.assessment
        questions = assessment.questions

        # Fetch saved responses
        responses = await self.assessment_repo.get_responses_for_attempt(attempt.id)
        resp_map: dict[UUID, AssessmentResponse] = {r.question_id: r for r in responses}

        total_questions = len(questions)
        correct_count = 0
        incorrect_count = 0
        unanswered_count = 0
        score_obtained = Decimal("0.00")
        total_score = Decimal("0.00")

        topic_stats: dict[str, dict[str, Any]] = {}

        for q in questions:
            q_marks = Decimal(str(q.marks))
            total_score += q_marks
            topic_name = q.topic.name if q.topic else "General"

            if topic_name not in topic_stats:
                topic_stats[topic_name] = {
                    "total_questions": 0,
                    "correct_answers": 0,
                    "incorrect_answers": 0,
                    "unanswered": 0,
                    "score_obtained": 0.0,
                    "total_score": 0.0,
                }

            topic_stats[topic_name]["total_questions"] += 1
            topic_stats[topic_name]["total_score"] += float(q_marks)

            resp = resp_map.get(q.id)
            selected = resp.selected_option.strip().upper() if (resp and resp.selected_option) else None
            corr = q.correct_option.strip().upper()

            if selected is None:
                # Unanswered
                unanswered_count += 1
                topic_stats[topic_name]["unanswered"] += 1
                if resp:
                    resp.is_correct = False
                    resp.marks_awarded = Decimal("0.00")
                else:
                    # Create unselected response record for audit trail
                    new_r = AssessmentResponse(
                        attempt_id=attempt.id,
                        question_id=q.id,
                        selected_option=None,
                        is_correct=False,
                        marks_awarded=Decimal("0.00"),
                        answered_at=None,
                    )
                    self.assessment_repo.session.add(new_r)
            elif selected == corr:
                # Correct
                correct_count += 1
                score_obtained += q_marks
                topic_stats[topic_name]["correct_answers"] += 1
                topic_stats[topic_name]["score_obtained"] += float(q_marks)
                resp.is_correct = True
                resp.marks_awarded = q_marks
            else:
                # Incorrect (0 marks in MVP)
                incorrect_count += 1
                topic_stats[topic_name]["incorrect_answers"] += 1
                resp.is_correct = False
                resp.marks_awarded = Decimal("0.00")

        # Percentage
        percentage = (
            (score_obtained / total_score * 100)
            if total_score > Decimal("0.00")
            else Decimal("0.00")
        )
        percentage = Decimal(str(round(percentage, 2)))
        is_passed = percentage >= assessment.pass_percentage

        time_taken = max(0, int((now - attempt.started_at).total_seconds()))
        max_duration_seconds = assessment.duration_minutes * 60
        if time_taken > max_duration_seconds:
            time_taken = max_duration_seconds

        result = AssessmentResult(
            attempt_id=attempt.id,
            score_obtained=score_obtained,
            total_score=total_score,
            percentage=percentage,
            is_passed=is_passed,
            total_questions=total_questions,
            correct_answers=correct_count,
            incorrect_answers=incorrect_count,
            unanswered=unanswered_count,
            time_taken_seconds=time_taken,
            topic_breakdown=topic_stats,
            created_at=now,
        )
        created_result = await self.assessment_repo.create_result(result)

        attempt.status = "EXPIRED" if is_expired else "SUBMITTED"
        attempt.submitted_at = now
        attempt.assignment.status = "COMPLETED"

        return created_result

    # -----------------------------------------------------------------------
    # Helper mappers
    # -----------------------------------------------------------------------

    def _to_summary(self, a: Assessment) -> AssessmentSummary:
        return AssessmentSummary(
            id=a.id,
            title=a.title,
            description=a.description,
            category_id=a.category_id,
            category_name=a.category.name if a.category else None,
            topic_id=a.topic_id,
            topic_name=a.topic.name if a.topic else None,
            role_id=a.role_id,
            role_name=a.role.name if a.role else None,
            placement_drive_id=a.placement_drive_id,
            placement_drive_title=a.placement_drive.title if a.placement_drive else None,
            difficulty=a.difficulty,
            duration_minutes=a.duration_minutes,
            total_marks=a.total_marks,
            pass_percentage=a.pass_percentage,
            status=a.status,
            allow_multiple_attempts=a.allow_multiple_attempts,
            questions_count=len(a.questions) if a.questions else 0,
            created_by_user_id=a.created_by_user_id,
            created_at=a.created_at,
            updated_at=a.updated_at,
        )

    def _to_assignment_response(self, a: AssessmentAssignment) -> AssessmentAssignmentResponse:
        assessment = a.assessment
        student = a.student
        latest_res = None
        if a.attempts:
            for att in reversed(a.attempts):
                if att.result:
                    latest_res = att.result
                    break

        return AssessmentAssignmentResponse(
            id=a.id,
            assessment_id=a.assessment_id,
            student_user_id=a.student_user_id,
            assigned_by_user_id=a.assigned_by_user_id,
            due_date=a.due_date,
            status=a.status,
            created_at=a.created_at,
            assessment_title=assessment.title if assessment else None,
            difficulty=assessment.difficulty if assessment else None,
            duration_minutes=assessment.duration_minutes if assessment else None,
            total_marks=assessment.total_marks if assessment else None,
            pass_percentage=assessment.pass_percentage if assessment else None,
            category_name=assessment.category.name if (assessment and assessment.category) else None,
            topic_name=assessment.topic.name if (assessment and assessment.topic) else None,
            placement_drive_title=assessment.placement_drive.title if (assessment and assessment.placement_drive) else None,
            student_name=student.full_name if student else None,
            student_email=student.email if student else None,
            latest_result_id=latest_res.id if latest_res else None,
            latest_score=latest_res.score_obtained if latest_res else None,
            latest_percentage=latest_res.percentage if latest_res else None,
            latest_passed=latest_res.is_passed if latest_res else None,
        )

    def _to_result_response(
        self, r: AssessmentResult, include_review: bool = True
    ) -> AssessmentResultResponse:
        attempt = r.attempt
        assessment = attempt.assignment.assessment

        review_list = None
        if include_review and assessment and assessment.questions:
            resp_map = {resp.question_id: resp for resp in attempt.responses}
            review_list = []
            for q in assessment.questions:
                resp = resp_map.get(q.id)
                selected = resp.selected_option if resp else None
                is_correct = resp.is_correct if resp else False
                marks_awarded = resp.marks_awarded if resp else Decimal("0.00")
                review_list.append(
                    QuestionReviewView(
                        id=q.id,
                        topic_id=q.topic_id,
                        topic_name=q.topic.name if q.topic else None,
                        question_text=q.question_text,
                        options=[OptionItem(**opt) for opt in q.options],
                        selected_option=selected,
                        correct_option=q.correct_option,
                        is_correct=is_correct,
                        marks_awarded=marks_awarded or Decimal("0.00"),
                        explanation=q.explanation,
                        sequence_order=q.sequence_order,
                    )
                )

        return AssessmentResultResponse(
            id=r.id,
            attempt_id=r.attempt_id,
            assessment_id=assessment.id,
            assessment_title=assessment.title,
            score_obtained=r.score_obtained,
            total_score=r.total_score,
            percentage=r.percentage,
            is_passed=r.is_passed,
            total_questions=r.total_questions,
            correct_answers=r.correct_answers,
            incorrect_answers=r.incorrect_answers,
            unanswered=r.unanswered,
            time_taken_seconds=r.time_taken_seconds,
            topic_breakdown=r.topic_breakdown,
            created_at=r.created_at,
            review=review_list,
        )
