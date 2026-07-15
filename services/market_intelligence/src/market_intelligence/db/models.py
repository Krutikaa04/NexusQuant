"""ORM models for the market schema (SPEC-004; SPEC-006 §4 ``market``).

Market data is **immutable** (SPEC-002 ADR-004): ticks and candles are append-only and
never updated. Instruments are versioned via ``revision`` — a metadata change writes a new
revision rather than mutating history.
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


# SQLite autoincrements only a native INTEGER PRIMARY KEY; keep BIGINT on Postgres.
AutoBigInt = BigInteger().with_variant(Integer, "sqlite")


class InstrumentRecord(Base):
    """Canonical instrument metadata, versioned by ``revision`` (SPEC-004 Instrument Master)."""

    __tablename__ = "instruments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    symbol: Mapped[str] = mapped_column(String(64), nullable=False)
    exchange: Mapped[str] = mapped_column(String(8), nullable=False)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    segment: Mapped[str] = mapped_column(String(8), nullable=False)
    isin: Mapped[str | None] = mapped_column(String(12), nullable=True)
    tick_size: Mapped[float] = mapped_column(Float, nullable=False, default=0.05)
    lot_size: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    sector: Mapped[str | None] = mapped_column(String(128), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(128), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    listing_status: Mapped[str] = mapped_column(String(16), nullable=False, default="listed")
    expiry: Mapped[date | None] = mapped_column(Date, nullable=True)
    strike: Mapped[float | None] = mapped_column(Float, nullable=True)
    option_type: Mapped[str | None] = mapped_column(String(2), nullable=True)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint("symbol", "exchange", "revision", name="uq_instrument_revision"),
        Index("ix_instruments_symbol", "symbol", "exchange"),
        Index("ix_instruments_current", "is_current"),
    )


class TickRecord(Base):
    """An immutable, append-only tick (SPEC-004 tick ingestion)."""

    __tablename__ = "ticks"

    id: Mapped[int] = mapped_column(AutoBigInt, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(64), nullable=False)
    exchange: Mapped[str] = mapped_column(String(8), nullable=False)
    ltp: Mapped[float] = mapped_column(Float, nullable=False)
    ltq: Mapped[int] = mapped_column(Integer, nullable=False)
    volume: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sequence: Mapped[int] = mapped_column(BigInteger, nullable=False)
    bid: Mapped[float | None] = mapped_column(Float, nullable=True)
    ask: Mapped[float | None] = mapped_column(Float, nullable=True)
    quality_score: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    exchange_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    received_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint("symbol", "exchange", "sequence", name="uq_tick_sequence"),
        Index("ix_ticks_symbol_time", "symbol", "exchange_ts"),
    )


class CandleRecord(Base):
    """An immutable OHLCV candle produced at bar close (SPEC-004 candle aggregation)."""

    __tablename__ = "candles"

    id: Mapped[int] = mapped_column(AutoBigInt, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(64), nullable=False)
    interval_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    open_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    close_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    open: Mapped[float] = mapped_column(Float, nullable=False)
    high: Mapped[float] = mapped_column(Float, nullable=False)
    low: Mapped[float] = mapped_column(Float, nullable=False)
    close: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[int] = mapped_column(BigInteger, nullable=False)
    tick_count: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        UniqueConstraint("symbol", "interval_seconds", "open_time", name="uq_candle_bar"),
        Index("ix_candles_symbol_interval_time", "symbol", "interval_seconds", "open_time"),
    )


class HolidayRecord(Base):
    """An exchange trading holiday (SPEC-004 Trading Calendar)."""

    __tablename__ = "trading_holidays"

    day: Mapped[date] = mapped_column(Date, primary_key=True)
    reason: Mapped[str] = mapped_column(String(256), nullable=False)


class SpecialSessionRecord(Base):
    """A non-regular trading window, e.g. Muhurat (SPEC-004 Trading Calendar)."""

    __tablename__ = "special_sessions"

    day: Mapped[date] = mapped_column(Date, primary_key=True)
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    open_time: Mapped[str] = mapped_column(String(5), nullable=False)  # "HH:MM" IST
    close_time: Mapped[str] = mapped_column(String(5), nullable=False)
    description: Mapped[str] = mapped_column(String(256), nullable=False)


class CorporateActionRecord(Base):
    """An immutable, versioned corporate action (SPEC-004 Corporate Actions Engine)."""

    __tablename__ = "corporate_actions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    symbol: Mapped[str] = mapped_column(String(64), nullable=False)
    exchange: Mapped[str] = mapped_column(String(8), nullable=False)
    action_type: Mapped[str] = mapped_column(String(16), nullable=False)
    ex_date: Mapped[date] = mapped_column(Date, nullable=False)
    details: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    # Monotonic per-symbol adjustment version: research datasets pin against this.
    adjustment_version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "symbol", "exchange", "action_type", "ex_date", name="uq_corp_action"
        ),
        Index("ix_corp_actions_symbol", "symbol", "ex_date"),
    )


class RegimeRecord(Base):
    """An append-only market-regime snapshot (SPEC-004 Market Regime Engine)."""

    __tablename__ = "market_regimes"

    id: Mapped[int] = mapped_column(AutoBigInt, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(64), nullable=False)
    regimes: Mapped[list] = mapped_column(JSON, nullable=False)
    indicators: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (Index("ix_regimes_symbol_time", "symbol", "created_at"),)


class DataQualityRecord(Base):
    """An append-only data-quality snapshot for a symbol (SPEC-004 Data Quality Engine)."""

    __tablename__ = "data_quality"

    id: Mapped[int] = mapped_column(AutoBigInt, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(64), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[str] = mapped_column(String(8), nullable=False)
    readiness: Mapped[str] = mapped_column(String(16), nullable=False)
    metrics: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (Index("ix_dq_symbol_time", "symbol", "created_at"),)
