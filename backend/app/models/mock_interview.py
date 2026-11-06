"""
CampusFlow — Mock Interview ORM Models.

Stores AI mock interview sessions and individual question evaluations,
enabling historical performance tracking and comprehensive report generation.
"""
from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class MockInterviewSession(Base):
    __tablename__ = "mock_interview_sessions"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    track_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    track_title: Mapped[str] = mapped_column(String(255), nullable=False)
    target_role: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(
        String(30), default="IN_PROGRESS", nullable=False, index=True
    )  # IN_PROGRESS, COMPLETED, ABANDONED

    # Aggregate Performance Metrics (0.0 - 100.0)
    overall_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    technical_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    communication_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    structure_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    performance_rating: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # EXCEPTIONAL, JOB_READY, DEVELOPING, NEEDS_PRACTICE
    summary_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Detailed structured feedback collections
    strengths: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    improvements: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    action_plan: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    topic_breakdown: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    user = relationship("User")
    evaluations: Mapped[list[MockInterviewEvaluation]] = relationship(
        "MockInterviewEvaluation",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="MockInterviewEvaluation.question_index",
        lazy="selectin",
    )


class MockInterviewEvaluation(Base):
    __tablename__ = "mock_interview_evaluations"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    session_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mock_interview_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_index: Mapped[int] = mapped_column(Integer, nullable=False)
    question_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_category: Mapped[str] = mapped_column(String(100), nullable=False)
    student_answer: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Audio & Speech metrics
    audio_duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    words_per_minute: Mapped[float | None] = mapped_column(Float, nullable=True)
    filler_words: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)

    # Scoring breakdown (0.0 - 100.0)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    technical_depth_score: Mapped[float] = mapped_column(Float, nullable=False)
    communication_score: Mapped[float] = mapped_column(Float, nullable=False)
    structure_score: Mapped[float] = mapped_column(Float, nullable=False)

    # AI Critique and Guidance
    feedback_critique: Mapped[str] = mapped_column(Text, nullable=False)
    strengths: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    improvements: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    ideal_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    keywords_matched: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    keywords_missed: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )

    # Relationships
    session: Mapped[MockInterviewSession] = relationship(
        "MockInterviewSession", back_populates="evaluations"
    )
