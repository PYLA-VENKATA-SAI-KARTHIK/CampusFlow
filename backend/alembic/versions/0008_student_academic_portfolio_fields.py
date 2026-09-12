"""add student academic marks, section, and portfolio fields

Revision ID: 0008_student_academic_portfolio
Revises: 0007_audit_logs_immutability
Create Date: 2026-09-12 21:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0008_student_academic_portfolio'
down_revision: Union[str, None] = '0007_audit_logs_immutability'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('student_profiles', sa.Column('section', sa.String(length=10), nullable=True))
    op.add_column('student_profiles', sa.Column('tenth_mark', sa.Numeric(precision=5, scale=2), nullable=True))
    op.add_column('student_profiles', sa.Column('twelfth_mark', sa.Numeric(precision=5, scale=2), nullable=True))
    op.add_column('student_profiles', sa.Column('diploma_mark', sa.Numeric(precision=5, scale=2), nullable=True))
    op.add_column('student_profiles', sa.Column('portfolio_url', sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column('student_profiles', 'portfolio_url')
    op.drop_column('student_profiles', 'diploma_mark')
    op.drop_column('student_profiles', 'twelfth_mark')
    op.drop_column('student_profiles', 'tenth_mark')
    op.drop_column('student_profiles', 'section')
