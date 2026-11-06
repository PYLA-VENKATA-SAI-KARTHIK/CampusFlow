"""add mock interview voice agent tables

Revision ID: 0012_mock_interview_voice_agent
Revises: 0011_practice_assessment_engine
Create Date: 2026-10-31 16:35:00.000000

"""
from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '0012_mock_interview_voice_agent'
down_revision: Union[str, None] = '0011_practice_assessment_engine'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. mock_interview_sessions
    op.create_table(
        'mock_interview_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('track_id', sa.String(length=50), nullable=False),
        sa.Column('track_title', sa.String(length=255), nullable=False),
        sa.Column('target_role', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=30), server_default='IN_PROGRESS', nullable=False),
        sa.Column('overall_score', sa.Float(), nullable=True),
        sa.Column('technical_score', sa.Float(), nullable=True),
        sa.Column('communication_score', sa.Float(), nullable=True),
        sa.Column('structure_score', sa.Float(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('performance_rating', sa.String(length=50), nullable=True),
        sa.Column('summary_feedback', sa.Text(), nullable=True),
        sa.Column('strengths', sa.JSON(), server_default='[]', nullable=False),
        sa.Column('improvements', sa.JSON(), server_default='[]', nullable=False),
        sa.Column('action_plan', sa.JSON(), server_default='[]', nullable=False),
        sa.Column('topic_breakdown', sa.JSON(), server_default='{}', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_mock_interview_sessions_user_id', 'mock_interview_sessions', ['user_id'])
    op.create_index('ix_mock_interview_sessions_track_id', 'mock_interview_sessions', ['track_id'])
    op.create_index('ix_mock_interview_sessions_status', 'mock_interview_sessions', ['status'])

    # 2. mock_interview_evaluations
    op.create_table(
        'mock_interview_evaluations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mock_interview_sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('question_index', sa.Integer(), nullable=False),
        sa.Column('question_id', sa.String(length=50), nullable=True),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('question_category', sa.String(length=100), nullable=False),
        sa.Column('student_answer', sa.Text(), nullable=False),
        sa.Column('audio_duration_seconds', sa.Float(), nullable=True),
        sa.Column('words_per_minute', sa.Float(), nullable=True),
        sa.Column('filler_words', sa.JSON(), server_default='[]', nullable=False),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('technical_depth_score', sa.Float(), nullable=False),
        sa.Column('communication_score', sa.Float(), nullable=False),
        sa.Column('structure_score', sa.Float(), nullable=False),
        sa.Column('feedback_critique', sa.Text(), nullable=False),
        sa.Column('strengths', sa.JSON(), server_default='[]', nullable=False),
        sa.Column('improvements', sa.JSON(), server_default='[]', nullable=False),
        sa.Column('ideal_response', sa.Text(), nullable=True),
        sa.Column('keywords_matched', sa.JSON(), server_default='[]', nullable=False),
        sa.Column('keywords_missed', sa.JSON(), server_default='[]', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_mock_interview_evaluations_session_id', 'mock_interview_evaluations', ['session_id'])


def downgrade() -> None:
    op.drop_table('mock_interview_evaluations')
    op.drop_table('mock_interview_sessions')
