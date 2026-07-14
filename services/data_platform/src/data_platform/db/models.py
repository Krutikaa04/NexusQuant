"""ORM models for the immutable artifact store (SPEC-006 §4, §5, §8).

Ownership note (reconciling SPEC-006 with SPEC-003): the Data Platform is the *system of
record for versioning and immutability* of datasets, features and models. Producing
contexts (Research OS, Alpha Factory) own the semantics and emit events; this store indexes
the resulting immutable, append-only artifact versions.

Conventions (SPEC-006 §8): UUID string primary keys, timezone-aware UTC timestamps,
soft-delete (``is_active``) permitted only on user-facing *metadata* — artifact versions
themselves are never updated or deleted.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Artifact(Base):
    """The identity of a versioned artifact (a dataset, feature, or model)."""

    __tablename__ = "artifacts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    namespace: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    owner_context: Mapped[str] = mapped_column(String(64), nullable=False)
    # Soft-delete for user-facing metadata only (SPEC-006 §8); versions are never removed.
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    versions: Mapped[list["ArtifactVersion"]] = relationship(
        back_populates="artifact", cascade="all, delete-orphan", order_by="ArtifactVersion.version"
    )

    __table_args__ = (
        UniqueConstraint("kind", "namespace", "name", name="uq_artifact_identity"),
        Index("ix_artifacts_kind", "kind"),
    )


class ArtifactVersion(Base):
    """An immutable, append-only version of an artifact (SPEC-006 §5)."""

    __tablename__ = "artifact_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    artifact_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("artifacts.id"), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    storage_uri: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    source_event_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    artifact: Mapped[Artifact] = relationship(back_populates="versions")

    __table_args__ = (
        UniqueConstraint("artifact_id", "version", name="uq_artifact_version"),
        UniqueConstraint("content_hash", name="uq_artifact_version_hash"),
        Index("ix_artifact_versions_artifact", "artifact_id", "version"),
    )


class LineageEdge(Base):
    """A directed edge in the data-lineage DAG (SPEC-006 §2 data lineage)."""

    __tablename__ = "lineage_edges"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    upstream_version_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("artifact_versions.id"), nullable=False
    )
    downstream_version_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("artifact_versions.id"), nullable=False
    )
    relation: Mapped[str] = mapped_column(String(64), nullable=False, default="derived_from")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "upstream_version_id", "downstream_version_id", "relation", name="uq_lineage_edge"
        ),
        Index("ix_lineage_downstream", "downstream_version_id"),
        Index("ix_lineage_upstream", "upstream_version_id"),
    )


class ReadModel(Base):
    """A materialised, cache-fronted projection for fast reads (SPEC-006 §2 read models)."""

    __tablename__ = "read_models"

    key: Mapped[str] = mapped_column(String(256), primary_key=True)
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    projection: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (Index("ix_read_models_kind", "kind"),)
