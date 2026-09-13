"""
Assessment Pydantic Schemas.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Options & Question Schemas
# ---------------------------------------------------------------------------

class OptionItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    key: str = Field(..., min_length=1, max_length=10, description="Option key e.g. A, B, C, D")
    text: str = Field(..., min_length=1, max_length=1000, description="Option display text")


class QuestionCreate(BaseModel):
    question_text: str = Field(..., min_length=3, description="Text of the question")
    options: list[OptionItem] = Field(..., min_length=2, max_length=10, description="List of MCQ options")
    correct_option: str = Field(..., min_length=1, max_length=10, description="Key of the correct option")
    explanation: str | None = Field(default=None, description="Explanation for post-submission review")
    marks: Decimal = Field(default=Decimal("1.00"), gt=0, le=100, description="Marks for correct answer")
    topic_id: UUID | None = Field(default=None, description="Preparation topic ID")
    sequence_order: int = Field(default=1, ge=1, description="Display order")

    @field_validator("options")
    @classmethod
    def validate_options(cls, v: list[OptionItem]) -> list[OptionItem]:
        keys = [opt.key.strip().upper() for opt in v]
        if len(keys) != len(set(keys)):
            raise ValueError("Option keys must be unique within a question")
        return v

    @model_validator(mode="after")
    def validate_correct_option_exists(self) -> QuestionCreate:
        opt_keys = {opt.key.strip().upper() for opt in self.options}
        if self.correct_option.strip().upper() not in opt_keys:
            raise ValueError(f"Correct option '{self.correct_option}' must match one of the option keys: {list(opt_keys)}")
        return self


class QuestionUpdate(BaseModel):
    question_text: str | None = Field(default=None, min_length=3)
    options: list[OptionItem] | None = Field(default=None, min_length=2, max_length=10)
    correct_option: str | None = Field(default=None, min_length=1, max_length=10)
    explanation: str | None = None
    marks: Decimal | None = Field(default=None, gt=0, le=100)
    topic_id: UUID | None = None
    sequence_order: int | None = Field(default=None, ge=1)

    @field_validator("options")
    @classmethod
    def validate_options(cls, v: list[OptionItem] | None) -> list[OptionItem] | None:
        if v is not None:
            keys = [opt.key.strip().upper() for opt in v]
            if len(keys) != len(set(keys)):
                raise ValueError("Option keys must be unique within a question")
        return v


class QuestionAdminView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    assessment_id: UUID
    topic_id: UUID | None = None
    topic_name: str | None = None
    question_text: str
    options: list[OptionItem]
    correct_option: str
    explanation: str | None = None
    marks: Decimal
    sequence_order: int
    created_at: datetime
    updated_at: datetime


class QuestionStudentView(BaseModel):
    """
    CRITICAL SECURITY GUARANTEE:
    This DTO is returned to students during active test taking.
    It MUST NEVER contain `correct_option` or `explanation`.
    """
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    assessment_id: UUID
    topic_id: UUID | None = None
    question_text: str
    options: list[OptionItem]
    marks: Decimal
    sequence_order: int


class QuestionReviewView(BaseModel):
    """
    DTO returned to students ONLY after test submission has been finalized.
    """
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    topic_id: UUID | None = None
    topic_name: str | None = None
    question_text: str
    options: list[OptionItem]
    selected_option: str | None = None
    correct_option: str
    is_correct: bool
    marks_awarded: Decimal
    explanation: str | None = None
    sequence_order: int


# ---------------------------------------------------------------------------
# Assessment Schemas
# ---------------------------------------------------------------------------

class AssessmentCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: str | None = None
    category_id: UUID | None = None
    topic_id: UUID | None = None
    role_id: UUID | None = None
    placement_drive_id: UUID | None = None
    difficulty: str = Field(default="BEGINNER", pattern="^(BEGINNER|INTERMEDIATE|ADVANCED)$")
    duration_minutes: int = Field(default=30, gt=0, le=360)
    pass_percentage: Decimal = Field(default=Decimal("50.00"), ge=0, le=100)
    allow_multiple_attempts: bool = False


class AssessmentUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=255)
    description: str | None = None
    category_id: UUID | None = None
    topic_id: UUID | None = None
    role_id: UUID | None = None
    placement_drive_id: UUID | None = None
    difficulty: str | None = Field(default=None, pattern="^(BEGINNER|INTERMEDIATE|ADVANCED)$")
    duration_minutes: int | None = Field(default=None, gt=0, le=360)
    pass_percentage: Decimal | None = Field(default=None, ge=0, le=100)
    allow_multiple_attempts: bool | None = None


class AssessmentSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str | None = None
    category_id: UUID | None = None
    category_name: str | None = None
    topic_id: UUID | None = None
    topic_name: str | None = None
    role_id: UUID | None = None
    role_name: str | None = None
    placement_drive_id: UUID | None = None
    placement_drive_title: str | None = None
    difficulty: str
    duration_minutes: int
    total_marks: Decimal
    pass_percentage: Decimal
    status: str
    allow_multiple_attempts: bool
    questions_count: int = 0
    created_by_user_id: UUID
    created_at: datetime
    updated_at: datetime


class AssessmentAdminDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str | None = None
    category_id: UUID | None = None
    category_name: str | None = None
    topic_id: UUID | None = None
    topic_name: str | None = None
    role_id: UUID | None = None
    role_name: str | None = None
    placement_drive_id: UUID | None = None
    placement_drive_title: str | None = None
    difficulty: str
    duration_minutes: int
    total_marks: Decimal
    pass_percentage: Decimal
    status: str
    allow_multiple_attempts: bool
    created_by_user_id: UUID
    created_at: datetime
    updated_at: datetime
    questions: list[QuestionAdminView] = []
    assignments_count: int = 0
    completed_count: int = 0


class AssessmentStudentPreview(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    assignment_id: UUID | None = None
    title: str
    description: str | None = None
    category_name: str | None = None
    topic_name: str | None = None
    role_name: str | None = None
    placement_drive_title: str | None = None
    difficulty: str
    duration_minutes: int
    question_count: int
    total_marks: Decimal
    pass_percentage: Decimal
    due_date: datetime | None = None
    assignment_status: str
    has_active_attempt: bool = False
    active_attempt_id: UUID | None = None
    active_attempt_expires_at: datetime | None = None
    latest_result_id: UUID | None = None
    latest_score: Decimal | None = None
    latest_percentage: Decimal | None = None
    latest_passed: bool | None = None


# ---------------------------------------------------------------------------
# Assignment Schemas
# ---------------------------------------------------------------------------

class AssessmentAssignRequest(BaseModel):
    student_user_ids: list[UUID] = Field(..., min_length=1)
    due_date: datetime | None = None


class AssessmentAssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    assessment_id: UUID
    student_user_id: UUID
    assigned_by_user_id: UUID | None = None
    due_date: datetime | None = None
    status: str
    created_at: datetime
    assessment_title: str | None = None
    difficulty: str | None = None
    duration_minutes: int | None = None
    total_marks: Decimal | None = None
    pass_percentage: Decimal | None = None
    category_name: str | None = None
    topic_name: str | None = None
    placement_drive_title: str | None = None
    student_name: str | None = None
    student_email: str | None = None
    student_roll_number: str | None = None
    student_branch: str | None = None
    latest_result_id: UUID | None = None
    latest_score: Decimal | None = None
    latest_percentage: Decimal | None = None
    latest_passed: bool | None = None


# ---------------------------------------------------------------------------
# Attempt & Response Schemas
# ---------------------------------------------------------------------------

class QuestionAnswerItem(BaseModel):
    question_id: UUID
    selected_option: str | None = None


class StartAttemptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    attempt_id: UUID
    assessment_id: UUID
    assignment_id: UUID
    title: str
    duration_minutes: int
    started_at: datetime
    expires_at: datetime
    questions: list[QuestionStudentView]
    saved_responses: dict[str, str | None] = {}


class SaveProgressRequest(BaseModel):
    responses: list[QuestionAnswerItem] = Field(..., min_length=1)


class SubmitAttemptRequest(BaseModel):
    responses: list[QuestionAnswerItem] | None = None


# ---------------------------------------------------------------------------
# Result Schemas
# ---------------------------------------------------------------------------

class AssessmentResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    attempt_id: UUID
    assessment_id: UUID
    assessment_title: str
    score_obtained: Decimal
    total_score: Decimal
    percentage: Decimal
    is_passed: bool
    total_questions: int
    correct_answers: int
    incorrect_answers: int
    unanswered: int
    time_taken_seconds: int
    topic_breakdown: dict[str, Any]
    created_at: datetime
    review: list[QuestionReviewView] | None = None


class OfficerAssessmentResultsView(BaseModel):
    assessment_id: UUID
    assessment_title: str
    total_assigned: int
    total_started: int
    total_completed: int
    average_score: Decimal | None = None
    average_percentage: Decimal | None = None
    pass_count: int
    results: list[AssessmentAssignmentResponse]
