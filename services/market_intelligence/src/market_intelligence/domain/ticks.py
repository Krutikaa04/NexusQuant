"""Tick domain types (SPEC-004 tick ingestion)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class RawTick:
    """A tick as delivered by a vendor adapter, before validation/normalisation."""

    symbol: str
    exchange: str
    ltp: float
    ltq: int
    volume: int
    sequence: int
    exchange_ts: datetime
    bid: float | None = None
    ask: float | None = None


@dataclass(frozen=True, slots=True)
class NormalizedTick:
    """A validated, normalised tick ready for persistence and publishing.

    Immutable market fact (SPEC-002 ADR-004): once produced it is never altered.
    """

    symbol: str
    exchange: str
    ltp: float
    ltq: int
    volume: int
    sequence: int
    exchange_ts: datetime
    received_ts: datetime
    bid: float | None
    ask: float | None
    quality_score: float
