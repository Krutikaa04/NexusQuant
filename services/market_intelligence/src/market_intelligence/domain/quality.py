"""Data-quality domain types (SPEC-004 Data Quality Engine).

Every tick contributes to a rolling, per-symbol quality assessment yielding a score, a
confidence level, and a *trading readiness* verdict that downstream execution can gate on.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class TradingReadiness(str, Enum):
    READY = "ready"
    DEGRADED = "degraded"
    BLOCKED = "blocked"


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RejectionReason(str, Enum):
    UNKNOWN_SYMBOL = "unknown_symbol"
    DUPLICATE = "duplicate"
    SEQUENCE_GAP = "sequence_gap"
    NON_MONOTONIC = "non_monotonic_sequence"
    TIMESTAMP_DRIFT = "timestamp_drift"
    INVALID_PRICE = "invalid_price"


@dataclass(frozen=True, slots=True)
class QualitySnapshot:
    """The current quality assessment for a symbol."""

    symbol: str
    score: float
    confidence: ConfidenceLevel
    readiness: TradingReadiness
    metrics: dict[str, float] = field(default_factory=dict)
