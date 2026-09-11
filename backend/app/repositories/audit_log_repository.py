"""
Audit Log repository.
"""
from __future__ import annotations

from datetime import datetime
from typing import Sequence
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


class AuditLogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def add(self, audit_log: AuditLog) -> None:
        self.session.add(audit_log)

    # -------------------------------------------------------------------------
    # Admin — Audit log listing (paginated, filtered)
    # -------------------------------------------------------------------------

    async def list_audit_logs(
        self,
        skip: int = 0,
        limit: int = 20,
        user_id: UUID | None = None,
        entity_type: str | None = None,
        action: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> tuple[Sequence[AuditLog], int]:
        """
        List audit logs with optional filters.
        Returns (logs, total_count).
        """
        base_stmt = select(AuditLog)

        if user_id is not None:
            base_stmt = base_stmt.where(AuditLog.performed_by_user_id == user_id)
        if entity_type is not None:
            base_stmt = base_stmt.where(AuditLog.entity_type == entity_type)
        if action is not None:
            base_stmt = base_stmt.where(AuditLog.action == action)
        if start_date is not None:
            base_stmt = base_stmt.where(AuditLog.created_at >= start_date)
        if end_date is not None:
            base_stmt = base_stmt.where(AuditLog.created_at <= end_date)

        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total = await self.session.scalar(count_stmt) or 0

        stmt = (
            base_stmt
            .order_by(AuditLog.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all(), total
