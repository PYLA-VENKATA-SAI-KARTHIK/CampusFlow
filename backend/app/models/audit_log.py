"""
AuditLog model.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    performed_by_user_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=True
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    entity_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), index=True, nullable=True
    )
    old_state: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    new_state: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(INET, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), index=True, nullable=False
    )

    # Relationships
    performed_by = relationship("User")


# Immutability trigger: prevent UPDATE and DELETE on audit_logs
from sqlalchemy import DDL, event

_audit_logs_func_ddl = DDL("""
CREATE OR REPLACE FUNCTION audit_logs_immutable()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'audit_logs table is immutable — updates and deletes are not permitted';
END;
$$ LANGUAGE plpgsql;
""")

_audit_logs_trigger_ddl = DDL("""
CREATE OR REPLACE TRIGGER audit_logs_no_update_or_delete
    BEFORE UPDATE OR DELETE ON audit_logs
    FOR EACH ROW
    EXECUTE FUNCTION audit_logs_immutable();
""")

event.listen(
    AuditLog.__table__,
    "after_create",
    _audit_logs_func_ddl.execute_if(dialect="postgresql"),
)
event.listen(
    AuditLog.__table__,
    "after_create",
    _audit_logs_trigger_ddl.execute_if(dialect="postgresql"),
)
