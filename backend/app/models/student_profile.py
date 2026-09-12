"""
Student Profile ORM model.
"""
from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Numeric, SmallInteger, String, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False
    )
    roll_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    branch_code: Mapped[str] = mapped_column(
        String(20), ForeignKey("branches.code"), nullable=False
    )
    batch_year: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    cgpa: Mapped[float] = mapped_column(Numeric(4, 2), nullable=False)
    active_backlogs: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    phone_number: Mapped[str | None] = mapped_column(String(15), nullable=True)
    personal_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    gender: Mapped[str | None] = mapped_column(String(10), nullable=True)
    section: Mapped[str | None] = mapped_column(String(10), nullable=True)
    tenth_mark: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    twelfth_mark: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    diploma_mark: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    portfolio_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    resume_gcs_path: Mapped[str | None] = mapped_column(String, nullable=True)
    resume_uploaded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    avatar_gcs_path: Mapped[str | None] = mapped_column(String, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), onupdate=text("now()"), nullable=False
    )

    # Relationships
    user = relationship("User", back_populates="student_profile")
    branch = relationship("Branch", back_populates="student_profiles")
