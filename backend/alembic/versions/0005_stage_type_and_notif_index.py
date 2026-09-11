"""Expand stage_type constraint and add notifications index

Revision ID: 0005_stage_type_and_notif_index
Revises: 0004_notifications
Create Date: 2026-09-09 22:27:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '0005_stage_type_and_notif_index'
down_revision: Union[str, None] = '0004_notifications'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop old stage_type check constraint and replace with expanded version
    op.drop_constraint('chk_stage_type', 'placement_stages', type_='check')
    op.create_check_constraint(
        'chk_stage_type',
        'placement_stages',
        "stage_type IN ('APTITUDE', 'TECHNICAL', 'HR', 'GD', 'CODING', 'OTHER')",
    )
    # Add compound index on notifications for efficient dedup queries (audit finding #3)
    op.create_index(
        'ix_notifications_type_ref',
        'notifications',
        ['notification_type', 'reference_id'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index('ix_notifications_type_ref', table_name='notifications')
    op.drop_constraint('chk_stage_type', 'placement_stages', type_='check')
    op.create_check_constraint(
        'chk_stage_type',
        'placement_stages',
        "stage_type IN ('APTITUDE', 'TECHNICAL', 'HR', 'GD')",
    )
