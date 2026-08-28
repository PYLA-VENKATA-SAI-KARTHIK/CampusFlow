"""initial schema

Revision ID: 0001
Revises: 
Create Date: 2026-08-27 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users
    op.create_table('users',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.Column('role', sa.String(length=20), nullable=False),
    sa.Column('full_name', sa.String(length=255), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('must_change_password', sa.Boolean(), nullable=False),
    sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_is_active'), 'users', ['is_active'], unique=False)
    op.create_index(op.f('ix_users_role'), 'users', ['role'], unique=False)

    # 2. branches (Decision C)
    op.create_table('branches',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('code', sa.String(length=20), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_branches_code'), 'branches', ['code'], unique=True)

    # Seed initial branches
    op.execute("""
        INSERT INTO branches (id, code, name, is_active) VALUES
        (gen_random_uuid(), 'CSE', 'Computer Science & Engineering', true),
        (gen_random_uuid(), 'ECE', 'Electronics & Communication Engineering', true),
        (gen_random_uuid(), 'IT', 'Information Technology', true),
        (gen_random_uuid(), 'MECH', 'Mechanical Engineering', true),
        (gen_random_uuid(), 'CIVIL', 'Civil Engineering', true),
        (gen_random_uuid(), 'EEE', 'Electrical & Electronics Engineering', true),
        (gen_random_uuid(), 'AI', 'Artificial Intelligence & Machine Learning', true),
        (gen_random_uuid(), 'DS', 'Data Science', true);
    """)

    # 3. student_profiles
    op.create_table('student_profiles',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('roll_number', sa.String(length=50), nullable=False),
    sa.Column('branch_code', sa.String(length=20), nullable=False),
    sa.Column('batch_year', sa.SmallInteger(), nullable=False),
    sa.Column('cgpa', sa.Numeric(precision=4, scale=2), nullable=False),
    sa.Column('active_backlogs', sa.SmallInteger(), nullable=False),
    sa.Column('phone_number', sa.String(length=15), nullable=True),
    sa.Column('gender', sa.String(length=10), nullable=True),
    sa.Column('resume_gcs_path', sa.String(), nullable=True),
    sa.Column('resume_uploaded_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('avatar_gcs_path', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['branch_code'], ['branches.code'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('roll_number'),
    sa.UniqueConstraint('user_id')
    )

    # 4. account_activations
    op.create_table('account_activations',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('token_hash', sa.String(length=64), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('used', sa.Boolean(), nullable=False),
    sa.Column('resend_count', sa.SmallInteger(), nullable=False),
    sa.Column('last_resent_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_account_activations_token_hash'), 'account_activations', ['token_hash'], unique=True)

    # 5. refresh_tokens
    op.create_table('refresh_tokens',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('token_hash', sa.String(length=64), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('revoked', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_refresh_tokens_token_hash'), 'refresh_tokens', ['token_hash'], unique=True)
    op.create_index(op.f('ix_refresh_tokens_user_id'), 'refresh_tokens', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_refresh_tokens_user_id'), table_name='refresh_tokens')
    op.drop_index(op.f('ix_refresh_tokens_token_hash'), table_name='refresh_tokens')
    op.drop_table('refresh_tokens')
    
    op.drop_index(op.f('ix_account_activations_token_hash'), table_name='account_activations')
    op.drop_table('account_activations')
    
    op.drop_table('student_profiles')
    
    op.drop_index(op.f('ix_branches_code'), table_name='branches')
    op.drop_table('branches')
    
    op.drop_index(op.f('ix_users_role'), table_name='users')
    op.drop_index(op.f('ix_users_is_active'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
