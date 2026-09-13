"""
Practice Assessment Engine ORM models.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Assessment(Base):
    __tablename__ = "assessments"
    __table_args__ = (
        CheckConstraint("difficulty IN ('BEGINNER', 'INTERMEDIATE', 'ADVANCED')", name="chk_assessment_difficulty"),
        CheckConstraint("status IN ('DRAFT', 'PUBLISHED', 'ARCHIVED')", name="chk_assessment_status"),
        CheckConstraint("duration_minutes > 0", name="chk_assessment_duration_positive"),
        CheckConstraint("pass_percentage >= 0 AND pass_percentage <= 100", name="chk_assessment_pass_pct_range"),
        CheckConstraint("total_marks >= 0", name="chk_assessment_total_marks_non_neg"),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("preparation_categories.id", ondelete="SET NULL"), nullable=True, index=True
    )
    topic_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("preparation_topics.id", ondelete="SET NULL"), nullable=True, index=True
    )
    role_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("preparation_roles.id", ondelete="SET NULL"), nullable=True, index=True
    )
    placement_drive_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("placement_drives.id", ondelete="SET NULL"), nullable=True, index=True
    )
    difficulty: Mapped[str] = mapped_column(String(20), default="BEGINNER", nullable=False)
    duration_minutes: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    total_marks: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=0.00, server_default="0.00", nullable=False)
    pass_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=50.00, server_default="50.00", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="DRAFT", server_default="DRAFT", index=True, nullable=False)
    allow_multiple_attempts: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"), nullable=False)

    created_by_user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), onupdate=text("now()"), nullable=False
    )

    # Relationships
    category = relationship("PreparationCategory")
    topic = relationship("PreparationTopic")
    role = relationship("PreparationRole")
    placement_drive = relationship("PlacementDrive")
    created_by = relationship("User", foreign_keys=[created_by_user_id])
    questions = relationship(
        "AssessmentQuestion",
        back_populates="assessment",
        cascade="all, delete-orphan",
        order_by="AssessmentQuestion.sequence_order",
    )
    assignments = relationship(
        "AssessmentAssignment",
        back_populates="assessment",
        cascade="all, delete-orphan",
    )


class AssessmentQuestion(Base):
    __tablename__ = "assessment_questions"
    __table_args__ = (
        CheckConstraint("marks > 0", name="chk_assessment_question_marks_positive"),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    assessment_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    topic_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("preparation_topics.id", ondelete="SET NULL"), nullable=True, index=True
    )
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    correct_option: Mapped[str] = mapped_column(String(10), nullable=False)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    marks: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=1.00, server_default="1.00", nullable=False)
    sequence_order: Mapped[int] = mapped_column(SmallInteger, default=1, server_default="1", nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), onupdate=text("now()"), nullable=False
    )

    # Relationships
    assessment = relationship("Assessment", back_populates="questions")
    topic = relationship("PreparationTopic")
    responses = relationship("AssessmentResponse", back_populates="question", cascade="all, delete-orphan")


class AssessmentAssignment(Base):
    __tablename__ = "assessment_assignments"
    __table_args__ = (
        UniqueConstraint("assessment_id", "student_user_id", name="uq_assessment_student_assignment"),
        CheckConstraint("status IN ('ASSIGNED', 'IN_PROGRESS', 'COMPLETED', 'EXPIRED')", name="chk_assessment_assignment_status"),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    assessment_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    assigned_by_user_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="ASSIGNED", server_default="ASSIGNED", index=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), onupdate=text("now()"), nullable=False
    )

    # Relationships
    assessment = relationship("Assessment", back_populates="assignments")
    student = relationship("User", foreign_keys=[student_user_id])
    assigned_by = relationship("User", foreign_keys=[assigned_by_user_id])
    attempts = relationship(
        "AssessmentAttempt",
        back_populates="assignment",
        cascade="all, delete-orphan",
        order_by="AssessmentAttempt.attempt_number",
    )


class AssessmentAttempt(Base):
    __tablename__ = "assessment_attempts"
    __table_args__ = (
        CheckConstraint("status IN ('IN_PROGRESS', 'SUBMITTED', 'EXPIRED', 'ABANDONED')", name="chk_assessment_attempt_status"),
        CheckConstraint("attempt_number > 0", name="chk_assessment_attempt_num_pos"),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    assignment_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("assessment_assignments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    attempt_number: Mapped[int] = mapped_column(SmallInteger, default=1, server_default="1", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="IN_PROGRESS", server_default="IN_PROGRESS", index=True, nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    assignment = relationship("AssessmentAssignment", back_populates="attempts")
    responses = relationship("AssessmentResponse", back_populates="attempt", cascade="all, delete-orphan")
    result = relationship("AssessmentResult", back_populates="attempt", uselist=False, cascade="all, delete-orphan")


class AssessmentResponse(Base):
    __tablename__ = "assessment_responses"
    __table_args__ = (
        UniqueConstraint("attempt_id", "question_id", name="uq_attempt_question_response"),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    attempt_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("assessment_attempts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("assessment_questions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    selected_option: Mapped[str | None] = mapped_column(String(10), nullable=True)
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    marks_awarded: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    answered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    attempt = relationship("AssessmentAttempt", back_populates="responses")
    question = relationship("AssessmentQuestion", back_populates="responses")


class AssessmentResult(Base):
    __tablename__ = "assessment_results"
    __table_args__ = (
        CheckConstraint("score_obtained >= 0", name="chk_result_score_non_neg"),
        CheckConstraint("total_score >= 0", name="chk_result_total_score_non_neg"),
        CheckConstraint("percentage >= 0", name="chk_result_percentage_non_neg"),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    attempt_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("assessment_attempts.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )
    score_obtained: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    total_score: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    is_passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    total_questions: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    correct_answers: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    incorrect_answers: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    unanswered: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    time_taken_seconds: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    topic_breakdown: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default="{}", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )

    # Relationships
    attempt = relationship("AssessmentAttempt", back_populates="result")
