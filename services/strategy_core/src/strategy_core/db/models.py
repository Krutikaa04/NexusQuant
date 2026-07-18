"""ORM models for the strategy schema.

Design invariants:
* **UUID primary keys** for the aggregate root, its versions and audit records.
* **UTC timestamps** (timezone-aware ``DateTime``); the service always writes UTC.
* **Immutable versions** — ``strategy_versions`` is append-only; a config/metadata change
  writes a new row rather than mutating an existing one.
* **Append-only audit** — every lifecycle transition and structural change is recorded.
* **Soft delete** — strategies carry ``deleted_at``; rows are never hard-deleted.
* Mutable operational **health** lives in its own one-row-per-strategy table, updated in
  place by future services (this context only stores the fields).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


# SQLite autoincrements only a native INTEGER PRIMARY KEY; keep BIGINT on Postgres.
AutoBigInt = BigInteger().with_variant(Integer, "sqlite")


class StrategyRecord(Base):
    """The Strategy aggregate root — denormalized 'current' view plus lifecycle state."""

    __tablename__ = "strategies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    category: Mapped[str] = mapped_column(String(64), nullable=False, default="uncategorized")
    owner: Mapped[str] = mapped_column(String(120), nullable=False, default="unknown")
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="draft", index=True)
    tags: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    current_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class StrategyVersionRecord(Base):
    """An immutable snapshot of a strategy's metadata + configuration at a point in time."""

    __tablename__ = "strategy_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    strategy_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("strategies.id"), nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    category: Mapped[str] = mapped_column(String(64), nullable=False, default="uncategorized")
    tags: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    change_summary: Mapped[str] = mapped_column(String(280), nullable=False, default="")
    created_by: Mapped[str] = mapped_column(String(120), nullable=False, default="unknown")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint("strategy_id", "version", name="uq_strategy_version"),
    )


class StrategyAuditRecord(Base):
    """Append-only audit trail. One row per structural change or lifecycle transition."""

    __tablename__ = "strategy_audit"

    id: Mapped[int] = mapped_column(AutoBigInt, primary_key=True, autoincrement=True)
    strategy_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("strategies.id"), nullable=False, index=True
    )
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    from_status: Mapped[str | None] = mapped_column(String(24), nullable=True)
    to_status: Mapped[str | None] = mapped_column(String(24), nullable=True)
    version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    detail: Mapped[str] = mapped_column(Text, nullable=False, default="")
    actor: Mapped[str] = mapped_column(String(120), nullable=False, default="unknown")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class StrategyHealthRecord(Base):
    """Mutable operational health — one row per strategy, updated in place downstream.

    This context only *stores* these fields with safe defaults; future services (validation,
    execution, monitoring) own the values. No analytics are computed here.
    """

    __tablename__ = "strategy_health"

    strategy_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("strategies.id"), primary_key=True
    )
    health_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_evaluation: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_execution: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    consecutive_failures: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    consecutive_successes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    trading_allowed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
