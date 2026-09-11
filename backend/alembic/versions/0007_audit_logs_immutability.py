"""enforce audit_logs immutability via trigger

Revision ID: 0007_audit_logs_immutability
Revises: 0006_push_subscriptions
Create Date: 2026-09-11 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '0007_audit_logs_immutability'
down_revision: Union[str, None] = '0006_push_subscriptions'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create immutability trigger function
    op.execute("""
    CREATE OR REPLACE FUNCTION audit_logs_immutable()
    RETURNS TRIGGER AS $$
    BEGIN
        RAISE EXCEPTION 'audit_logs table is immutable — updates and deletes are not permitted';
    END;
    $$ LANGUAGE plpgsql;
    """)

    # 2. Attach trigger to audit_logs for UPDATE and DELETE
    op.execute("""
    CREATE TRIGGER audit_logs_no_update_or_delete
        BEFORE UPDATE OR DELETE ON audit_logs
        FOR EACH ROW
        EXECUTE FUNCTION audit_logs_immutable();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS audit_logs_no_update_or_delete ON audit_logs;")
    op.execute("DROP FUNCTION IF EXISTS audit_logs_immutable();")
