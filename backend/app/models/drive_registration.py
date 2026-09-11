"""
Drive Registration model.
"""
from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DriveRegistration(Base):
    __tablename__ = "drive_registrations"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    drive_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("placement_drives.id"), index=True, nullable=False
    )
    student_user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=False
    )
    resume_gcs_path_at_registration: Mapped[str] = mapped_column(
        Text, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(30), default="REGISTERED", index=True, nullable=False
    )
    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), onupdate=text("now()"), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("drive_id", "student_user_id", name="uix_drive_student_registration"),
    )

    # Relationships
    drive = relationship("PlacementDrive", back_populates="registrations")
    student = relationship("User", back_populates="drive_registrations")
