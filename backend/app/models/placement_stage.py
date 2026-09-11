"""
Placement Stage ORM model.
"""
from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, SmallInteger, String, Text, UniqueConstraint, text, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PlacementStage(Base):
    __tablename__ = "placement_stages"
    __table_args__ = (
        UniqueConstraint("drive_id", "sequence_order", name="uq_stage_drive_sequence"),
        CheckConstraint("stage_type IN ('APTITUDE', 'TECHNICAL', 'HR', 'GD', 'CODING', 'OTHER')", name="chk_stage_type"),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    drive_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("placement_drives.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    stage_type: Mapped[str] = mapped_column(String(50), nullable=False)
    sequence_order: Mapped[int] = mapped_column(SmallInteger, nullable=False, index=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    location_or_link: Mapped[str | None] = mapped_column(Text, nullable=True)
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), onupdate=text("now()"), nullable=False
    )

    # Relationships
    drive = relationship("PlacementDrive", back_populates="stages")
    assignments = relationship("StageAssignment", back_populates="stage", cascade="all, delete-orphan")
