"""Tick domain types (SPEC-004 tick ingestion)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class RawTick:
    """A tick as delivered by a vendor adapter, before validation/normalisation.

    ``received_ts`` is stamped by the collector at arrival: it is a property of
    *collection*, not processing, so replayed or simulated feeds carry their own arrival
    times and drift measurement stays meaningful. ``None`` means "arriving now".
    """

    symbol: str
    exchange: str
    ltp: float
    ltq: int
    volume: int
    sequence: int
    exchange_ts: datetime
    bid: float | None = None
    ask: float | None = None
    received_ts: datetime | None = None


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
