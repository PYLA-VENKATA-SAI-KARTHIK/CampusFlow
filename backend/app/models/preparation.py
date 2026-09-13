"""
Preparation Hub ORM models.
"""
from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PreparationRole(Base):
    __tablename__ = "preparation_roles"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), onupdate=text("now()"), nullable=False
    )

    # Relationships
    role_topics = relationship("PreparationRoleTopic", back_populates="role", cascade="all, delete-orphan")
    materials = relationship("PreparationMaterial", back_populates="role")


class PreparationCategory(Base):
    __tablename__ = "preparation_categories"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True)
    sequence_order: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), onupdate=text("now()"), nullable=False
    )

    # Relationships
    topics = relationship("PreparationTopic", back_populates="category", cascade="all, delete-orphan", order_by="PreparationTopic.name")


class PreparationTopic(Base):
    __tablename__ = "preparation_topics"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    category_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("preparation_categories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    slug: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), onupdate=text("now()"), nullable=False
    )

    # Relationships
    category = relationship("PreparationCategory", back_populates="topics")
    role_topics = relationship("PreparationRoleTopic", back_populates="topic", cascade="all, delete-orphan")
    materials = relationship("PreparationMaterial", back_populates="topic", cascade="all, delete-orphan")


class PreparationRoleTopic(Base):
    __tablename__ = "preparation_role_topics"
    __table_args__ = (
        UniqueConstraint("role_id", "topic_id", name="uq_role_topic"),
        CheckConstraint("importance IN ('CORE', 'ELECTIVE', 'BONUS')", name="chk_role_topic_importance"),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    role_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("preparation_roles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    topic_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("preparation_topics.id", ondelete="CASCADE"), nullable=False, index=True
    )
    importance: Mapped[str] = mapped_column(String(20), default="CORE", nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )

    # Relationships
    role = relationship("PreparationRole", back_populates="role_topics")
    topic = relationship("PreparationTopic", back_populates="role_topics")


class PreparationMaterial(Base):
    __tablename__ = "preparation_materials"
    __table_args__ = (
        CheckConstraint(
            "material_type IN ('ARTICLE', 'VIDEO', 'PDF', 'PRACTICE_QUESTIONS', 'DOCUMENTATION', 'COURSE', 'OTHER')",
            name="chk_material_type",
        ),
        CheckConstraint(
            "difficulty IN ('BEGINNER', 'INTERMEDIATE', 'ADVANCED')",
            name="chk_material_difficulty",
        ),
        CheckConstraint(
            "status IN ('PENDING', 'APPROVED', 'REJECTED')",
            name="chk_material_status",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    topic_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("preparation_topics.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("preparation_roles.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    material_type: Mapped[str] = mapped_column(String(50), default="ARTICLE", nullable=False)
    difficulty: Mapped[str] = mapped_column(String(20), default="BEGINNER", nullable=False)
    source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="APPROVED", nullable=False, index=True)

    submitted_by_user_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    reviewed_by_user_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), onupdate=text("now()"), nullable=False
    )

    # Relationships
    topic = relationship("PreparationTopic", back_populates="materials")
    role = relationship("PreparationRole", back_populates="materials")
    submitted_by = relationship("User", foreign_keys=[submitted_by_user_id])
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_user_id])
