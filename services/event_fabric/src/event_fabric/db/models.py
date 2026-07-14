"""SQLAlchemy models for the Event Fabric tables (SPEC-005 §8).

Design notes:
* ``sequence`` is a monotonic surrogate key providing a **total order** across all events
  and a stable cursor for deterministic replay (SPEC-005 §10). Per-aggregate ordering
  (SPEC-005 §5) is the projection of this total order onto a single ``aggregate_id``.
* ``event_id`` is the domain identity (UUID) and is unique.
* Rows are append-only and never updated — the event store is immutable (SPEC-002 ADR-004).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    DateTime,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


# A 64-bit autoincrement surrogate key. SQLite only autoincrements a native
# ``INTEGER PRIMARY KEY`` (the rowid), so on SQLite we fall back to INTEGER while keeping
# BIGINT on Postgres for the full 64-bit range.
AutoBigInt = BigInteger().with_variant(Integer, "sqlite")


class EventRecord(Base):
    """An immutable persisted domain event (table ``event_store``)."""

    __tablename__ = "event_store"

    sequence: Mapped[int] = mapped_column(AutoBigInt, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    event_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    timestamp_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    producer: Mapped[str] = mapped_column(String(64), nullable=False)
    correlation_id: Mapped[str] = mapped_column(String(36), nullable=False)
    aggregate_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    event_metadata: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)

    __table_args__ = (
        Index("ix_event_store_event_type", "event_type"),
        Index("ix_event_store_timestamp_utc", "timestamp_utc"),
        Index("ix_event_store_correlation_id", "correlation_id"),
        Index("ix_event_store_aggregate", "aggregate_id", "sequence"),
    )


class ConsumerOffset(Base):
    """The last sequence a named consumer has durably processed (table ``consumer_offsets``).

    Enables at-least-once delivery with idempotent consumers (SPEC-005 §5): a consumer
    resumes from ``last_sequence`` and safely re-processes anything it may have already
    seen because its handlers are idempotent.
    """

    __tablename__ = "consumer_offsets"

    consumer_name: Mapped[str] = mapped_column(String(128), primary_key=True)
    last_sequence: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class EventSchemaVersion(Base):
    """A record that a given event type/version schema has been registered (§8)."""

    __tablename__ = "event_schema_versions"

    event_type: Mapped[str] = mapped_column(String(128), primary_key=True)
    version: Mapped[int] = mapped_column(Integer, primary_key=True)
    registered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class DeadLetterEvent(Base):
    """An event that could not be accepted (table ``dead_letter_events``, SPEC-005 §5).

    Captures invalid-schema, unknown-version, and processing-failure envelopes together
    with the failure reason for later inspection and manual replay.
    """

    __tablename__ = "dead_letter_events"

    id: Mapped[int] = mapped_column(AutoBigInt, primary_key=True, autoincrement=True)
    event_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    event_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    event_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reason: Mapped[str] = mapped_column(String(64), nullable=False)
    error_detail: Mapped[str] = mapped_column(String, nullable=False)
    envelope: Mapped[dict] = mapped_column(JSON, nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint("event_id", "reason", name="uq_dlq_event_reason"),
        Index("ix_dlq_reason", "reason"),
    )
