"""placement drives

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-28 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0002'
down_revision: Union[str, None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. companies
    op.create_table('companies',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('website', sa.Text(), nullable=True),
    sa.Column('logo_gcs_path', sa.Text(), nullable=True),
    sa.Column('industry', sa.String(length=100), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('created_by_user_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )

    # 2. placement_drives
    op.create_table('placement_drives',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('job_role', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('ctc_lpa', sa.Numeric(precision=6, scale=2), nullable=True),
    sa.Column('stipend_monthly', sa.Numeric(precision=8, scale=2), nullable=True),
    sa.Column('location', sa.String(length=255), nullable=True),
    sa.Column('bond_details', sa.Text(), nullable=True),
    sa.Column('registration_deadline', sa.DateTime(timezone=True), nullable=True),
    sa.Column('status', sa.String(length=30), nullable=False),
    sa.Column('created_by_user_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
    sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_placement_drives_company_id'), 'placement_drives', ['company_id'], unique=False)
    op.create_index(op.f('ix_placement_drives_registration_deadline'), 'placement_drives', ['registration_deadline'], unique=False)
    op.create_index(op.f('ix_placement_drives_status'), 'placement_drives', ['status'], unique=False)

    # 3. eligibility_criteria
    op.create_table('eligibility_criteria',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('drive_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('criteria', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['drive_id'], ['placement_drives.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('drive_id')
    )
    # Add GIN index on criteria
    op.execute("CREATE INDEX ix_eligibility_criteria_gin ON eligibility_criteria USING GIN (criteria)")

    # 4. audit_logs
    op.create_table('audit_logs',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('performed_by_user_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('action', sa.String(length=100), nullable=False),
    sa.Column('entity_type', sa.String(length=50), nullable=False),
    sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('old_state', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('new_state', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('ip_address', postgresql.INET(), nullable=True),
    sa.Column('user_agent', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['performed_by_user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_logs_created_at'), 'audit_logs', ['created_at'], unique=False)
    op.create_index(op.f('ix_audit_logs_entity_id'), 'audit_logs', ['entity_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_entity_type'), 'audit_logs', ['entity_type'], unique=False)
    op.create_index(op.f('ix_audit_logs_performed_by_user_id'), 'audit_logs', ['performed_by_user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_audit_logs_performed_by_user_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_entity_type'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_entity_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_created_at'), table_name='audit_logs')
    op.drop_table('audit_logs')

    op.execute("DROP INDEX ix_eligibility_criteria_gin")
    op.drop_table('eligibility_criteria')

    op.drop_index(op.f('ix_placement_drives_status'), table_name='placement_drives')
    op.drop_index(op.f('ix_placement_drives_registration_deadline'), table_name='placement_drives')
    op.drop_index(op.f('ix_placement_drives_company_id'), table_name='placement_drives')
    op.drop_table('placement_drives')

    op.drop_table('companies')
