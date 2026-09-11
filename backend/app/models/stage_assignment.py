"""
Stage Assignment ORM model.
"""
from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, text, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class StageAssignment(Base):
    __tablename__ = "stage_assignments"
    __table_args__ = (
        UniqueConstraint("stage_id", "student_user_id", name="uq_assignment_stage_student"),
        CheckConstraint("status IN ('SHORTLISTED', 'APPEARED', 'SELECTED', 'REJECTED')", name="chk_assignment_status"),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    stage_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("placement_stages.id"), nullable=False, index=True
    )
    student_user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    # Denormalized for query efficiency
    drive_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("placement_drives.id"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="SHORTLISTED", index=True)
    result_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), onupdate=text("now()"), nullable=False
    )

    # Relationships
    stage = relationship("PlacementStage", back_populates="assignments")
    student = relationship("User")
    drive = relationship("PlacementDrive")
