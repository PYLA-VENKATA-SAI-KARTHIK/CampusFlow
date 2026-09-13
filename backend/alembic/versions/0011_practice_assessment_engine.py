"""add practice assessment engine tables

Revision ID: 0011_practice_assessment_engine
Revises: 0010_preparation_hub
Create Date: 2026-09-13 10:30:00.000000

"""
from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '0011_practice_assessment_engine'
down_revision: Union[str, None] = '0010_preparation_hub'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. assessments
    op.create_table(
        'assessments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('preparation_categories.id', ondelete='SET NULL'), nullable=True),
        sa.Column('topic_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('preparation_topics.id', ondelete='SET NULL'), nullable=True),
        sa.Column('role_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('preparation_roles.id', ondelete='SET NULL'), nullable=True),
        sa.Column('placement_drive_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('placement_drives.id', ondelete='SET NULL'), nullable=True),
        sa.Column('difficulty', sa.String(length=20), server_default='BEGINNER', nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=False),
        sa.Column('total_marks', sa.Numeric(precision=6, scale=2), server_default='0.00', nullable=False),
        sa.Column('pass_percentage', sa.Numeric(precision=5, scale=2), server_default='50.00', nullable=False),
        sa.Column('status', sa.String(length=20), server_default='DRAFT', nullable=False),
        sa.Column('allow_multiple_attempts', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('created_by_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("difficulty IN ('BEGINNER', 'INTERMEDIATE', 'ADVANCED')", name='chk_assessment_difficulty'),
        sa.CheckConstraint("status IN ('DRAFT', 'PUBLISHED', 'ARCHIVED')", name='chk_assessment_status'),
        sa.CheckConstraint("duration_minutes > 0", name='chk_assessment_duration_positive'),
        sa.CheckConstraint("pass_percentage >= 0 AND pass_percentage <= 100", name='chk_assessment_pass_pct_range'),
        sa.CheckConstraint("total_marks >= 0", name='chk_assessment_total_marks_non_neg'),
    )
    op.create_index('ix_assessments_status', 'assessments', ['status'])
    op.create_index('ix_assessments_topic_id', 'assessments', ['topic_id'])
    op.create_index('ix_assessments_category_id', 'assessments', ['category_id'])
    op.create_index('ix_assessments_role_id', 'assessments', ['role_id'])
    op.create_index('ix_assessments_placement_drive_id', 'assessments', ['placement_drive_id'])
    op.create_index('ix_assessments_created_by', 'assessments', ['created_by_user_id'])

    # 2. assessment_questions
    op.create_table(
        'assessment_questions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('assessment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('assessments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('topic_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('preparation_topics.id', ondelete='SET NULL'), nullable=True),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('options', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('correct_option', sa.String(length=10), nullable=False),
        sa.Column('explanation', sa.Text(), nullable=True),
        sa.Column('marks', sa.Numeric(precision=6, scale=2), server_default='1.00', nullable=False),
        sa.Column('sequence_order', sa.SmallInteger(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("marks > 0", name='chk_assessment_question_marks_positive'),
    )
    op.create_index('ix_assessment_questions_assessment_id', 'assessment_questions', ['assessment_id'])
    op.create_index('ix_assessment_questions_topic_id', 'assessment_questions', ['topic_id'])

    # 3. assessment_assignments
    op.create_table(
        'assessment_assignments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('assessment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('assessments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('student_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('assigned_by_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='ASSIGNED', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('assessment_id', 'student_user_id', name='uq_assessment_student_assignment'),
        sa.CheckConstraint("status IN ('ASSIGNED', 'IN_PROGRESS', 'COMPLETED', 'EXPIRED')", name='chk_assessment_assignment_status'),
    )
    op.create_index('ix_assessment_assignments_assessment_id', 'assessment_assignments', ['assessment_id'])
    op.create_index('ix_assessment_assignments_student_user_id', 'assessment_assignments', ['student_user_id'])
    op.create_index('ix_assessment_assignments_status', 'assessment_assignments', ['status'])
    op.create_index('ix_assessment_assignments_student_status', 'assessment_assignments', ['student_user_id', 'status'])

    # 4. assessment_attempts
    op.create_table(
        'assessment_attempts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('assignment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('assessment_assignments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('attempt_number', sa.SmallInteger(), server_default='1', nullable=False),
        sa.Column('status', sa.String(length=20), server_default='IN_PROGRESS', nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("status IN ('IN_PROGRESS', 'SUBMITTED', 'EXPIRED', 'ABANDONED')", name='chk_assessment_attempt_status'),
        sa.CheckConstraint("attempt_number > 0", name='chk_assessment_attempt_num_pos'),
    )
    op.create_index('ix_assessment_attempts_assignment_id', 'assessment_attempts', ['assignment_id'])
    op.create_index('ix_assessment_attempts_status', 'assessment_attempts', ['status'])

    # 5. assessment_responses
    op.create_table(
        'assessment_responses',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('attempt_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('assessment_attempts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('question_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('assessment_questions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('selected_option', sa.String(length=10), nullable=True),
        sa.Column('is_correct', sa.Boolean(), nullable=True),
        sa.Column('marks_awarded', sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column('answered_at', sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint('attempt_id', 'question_id', name='uq_attempt_question_response'),
    )
    op.create_index('ix_assessment_responses_attempt_id', 'assessment_responses', ['attempt_id'])
    op.create_index('ix_assessment_responses_question_id', 'assessment_responses', ['question_id'])

    # 6. assessment_results
    op.create_table(
        'assessment_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('attempt_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('assessment_attempts.id', ondelete='CASCADE'), unique=True, nullable=False),
        sa.Column('score_obtained', sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column('total_score', sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column('percentage', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('is_passed', sa.Boolean(), nullable=False),
        sa.Column('total_questions', sa.SmallInteger(), nullable=False),
        sa.Column('correct_answers', sa.SmallInteger(), nullable=False),
        sa.Column('incorrect_answers', sa.SmallInteger(), nullable=False),
        sa.Column('unanswered', sa.SmallInteger(), nullable=False),
        sa.Column('time_taken_seconds', sa.Integer(), nullable=False),
        sa.Column('topic_breakdown', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("score_obtained >= 0", name='chk_result_score_non_neg'),
        sa.CheckConstraint("total_score >= 0", name='chk_result_total_score_non_neg'),
        sa.CheckConstraint("percentage >= 0", name='chk_result_percentage_non_neg'),
    )
    op.create_index('ix_assessment_results_attempt_id', 'assessment_results', ['attempt_id'], unique=True)


def downgrade() -> None:
    op.drop_table('assessment_results')
    op.drop_table('assessment_responses')
    op.drop_table('assessment_attempts')
    op.drop_table('assessment_assignments')
    op.drop_table('assessment_questions')
    op.drop_table('assessments')
