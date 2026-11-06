"""
CampusFlow — Mock Interview Voice Agent Schemas.
"""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MockInterviewSessionCreate(BaseModel):
    track_id: str = Field(..., min_length=1, max_length=50)
    track_title: str = Field(..., min_length=1, max_length=255)
    target_role: str | None = Field(default=None, max_length=255)


class MockInterviewEvaluateRequest(BaseModel):
    question_index: int = Field(..., ge=0)
    question_id: str | None = Field(default=None, max_length=50)
    question_text: str = Field(..., min_length=3)
    question_category: str = Field(..., min_length=1, max_length=100)
    student_answer: str = Field(..., min_length=1)
    expected_keywords: list[str] = Field(default_factory=list)
    coaching_tips: str | None = None
    audio_duration_seconds: float | None = Field(default=None, ge=0.0)


class MockInterviewEvaluationItem(BaseModel):
    id: UUID
    session_id: UUID
    question_index: int
    question_id: str | None = None
    question_text: str
    question_category: str
    student_answer: str
    audio_duration_seconds: float | None = None
    words_per_minute: float | None = None
    filler_words: list[str] = []
    score: float
    technical_depth_score: float
    communication_score: float
    structure_score: float
    feedback_critique: str
    strengths: list[str] = []
    improvements: list[str] = []
    ideal_response: str | None = None
    keywords_matched: list[str] = []
    keywords_missed: list[str] = []
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MockInterviewSessionResponse(BaseModel):
    id: UUID
    user_id: UUID
    track_id: str
    track_title: str
    target_role: str | None = None
    status: str
    overall_score: float | None = None
    technical_score: float | None = None
    communication_score: float | None = None
    structure_score: float | None = None
    confidence_score: float | None = None
    performance_rating: str | None = None
    summary_feedback: str | None = None
    strengths: list[str] = []
    improvements: list[str] = []
    action_plan: list[str] = []
    topic_breakdown: dict = {}
    evaluations: list[MockInterviewEvaluationItem] = []
    created_at: datetime
    completed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class MockInterviewSessionSummary(BaseModel):
    id: UUID
    track_id: str
    track_title: str
    target_role: str | None = None
    status: str
    overall_score: float | None = None
    performance_rating: str | None = None
    questions_count: int = 0
    created_at: datetime
    completed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
