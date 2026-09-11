"""drive_registrations

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-04 23:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0003'
down_revision: Union[str, None] = '0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('drive_registrations',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('drive_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('student_user_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('resume_gcs_path_at_registration', sa.Text(), nullable=False),
    sa.Column('status', sa.String(length=30), nullable=False),
    sa.Column('registered_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['drive_id'], ['placement_drives.id'], ),
    sa.ForeignKeyConstraint(['student_user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('drive_id', 'student_user_id', name='uix_drive_student_registration')
    )
    op.create_index(op.f('ix_drive_registrations_drive_id'), 'drive_registrations', ['drive_id'], unique=False)
    op.create_index(op.f('ix_drive_registrations_status'), 'drive_registrations', ['status'], unique=False)
    op.create_index(op.f('ix_drive_registrations_student_user_id'), 'drive_registrations', ['student_user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_drive_registrations_student_user_id'), table_name='drive_registrations')
    op.drop_index(op.f('ix_drive_registrations_status'), table_name='drive_registrations')
    op.drop_index(op.f('ix_drive_registrations_drive_id'), table_name='drive_registrations')
    op.drop_table('drive_registrations')
