"""
PlacementDrive model.
"""
from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PlacementDrive(Base):
    __tablename__ = "placement_drives"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    company_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("companies.id"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    job_role: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    ctc_lpa: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    stipend_monthly: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    bond_details: Mapped[str | None] = mapped_column(Text, nullable=True)
    registration_deadline: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), index=True, nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(30), default="DRAFT", index=True, nullable=False
    )
    created_by_user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), onupdate=text("now()"), nullable=False
    )

    # Relationships
    company = relationship("Company", back_populates="placement_drives")
    created_by = relationship("User")
    eligibility_criteria = relationship(
        "EligibilityCriteria", back_populates="drive", uselist=False
    )
