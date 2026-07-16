"""ORM models for the research schema (SPEC-007 §5).

Conventions (SPEC-006 §8): UUID string primary keys, timezone-aware UTC timestamps.
Reviews and status-history rows are **append-only** — immutable once written (SPEC-007:
"Every review must be immutable after completion"; §11 immutable audit trail).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class ProjectRecord(Base):
    """A research project — the aggregate root of the Research OS (SPEC-007 §5)."""

    __tablename__ = "research_projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    owner: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="draft")
    tags: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    extra: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    hypotheses: Mapped[list["HypothesisRecord"]] = relationship(
        back_populates="project", cascade="all, delete-orphan", order_by="HypothesisRecord.created_at"
    )
    experiments: Mapped[list["ExperimentRecord"]] = relationship(
        back_populates="project", cascade="all, delete-orphan", order_by="ExperimentRecord.created_at"
    )
    reviews: Mapped[list["ReviewRecord"]] = relationship(
        back_populates="project", cascade="all, delete-orphan", order_by="ReviewRecord.created_at"
    )

    __table_args__ = (
        Index("ix_projects_owner", "owner"),
        Index("ix_projects_status", "status"),
    )


class HypothesisRecord(Base):
    """A research question to validate (SPEC-007 §5)."""

    __tablename__ = "hypotheses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("research_projects.id"), nullable=False
    )
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    success_criteria: Mapped[str] = mapped_column(Text, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    project: Mapped[ProjectRecord] = relationship(back_populates="hypotheses")

    __table_args__ = (Index("ix_hypotheses_project", "project_id"),)


class ExperimentRecord(Base):
    """A controlled evaluation referencing explicit dataset/feature versions (§5, §8)."""

    __tablename__ = "experiments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("research_projects.id"), nullable=False
    )
    hypothesis_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("hypotheses.id"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    dataset_version: Mapped[str] = mapped_column(String(128), nullable=False)
    feature_version: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    metrics: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    project: Mapped[ProjectRecord] = relationship(back_populates="experiments")

    __table_args__ = (
        Index("ix_experiments_project", "project_id"),
        Index("ix_experiments_status", "status"),
    )


class ReviewRecord(Base):
    """An immutable governance review (SPEC-007 §5; append-only)."""

    __tablename__ = "research_reviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("research_projects.id"), nullable=False
    )
    reviewer: Mapped[str] = mapped_column(String(128), nullable=False)
    decision: Mapped[str] = mapped_column(String(16), nullable=False)
    comments: Mapped[str] = mapped_column(Text, nullable=False)
    # Project status at the moment of review — makes approvals stage-specific.
    stage: Mapped[str] = mapped_column(String(24), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    project: Mapped[ProjectRecord] = relationship(back_populates="reviews")

    __table_args__ = (Index("ix_reviews_project", "project_id"),)


class StatusHistoryRecord(Base):
    """Append-only record of every lifecycle transition (SPEC-007 §11 audit trail)."""

    __tablename__ = "research_status_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("research_projects.id"), nullable=False
    )
    from_status: Mapped[str | None] = mapped_column(String(24), nullable=True)
    to_status: Mapped[str] = mapped_column(String(24), nullable=False)
    actor: Mapped[str] = mapped_column(String(128), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (Index("ix_status_history_project", "project_id", "created_at"),)
