"""add personal_email column to student_profiles

Revision ID: 0009_student_personal_email
Revises: 0008_student_academic_portfolio
Create Date: 2026-09-12 22:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0009_student_personal_email'
down_revision: Union[str, None] = '0008_student_academic_portfolio'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('student_profiles', sa.Column('personal_email', sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column('student_profiles', 'personal_email')
