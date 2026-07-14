"""Data Quality Engine (SPEC-004 Data Quality Engine).

Maintains a rolling, per-symbol window of validation outcomes and derives a quality score,
a confidence level, and a trading-readiness verdict. When readiness transitions (e.g.
READY → DEGRADED), :meth:`observe` reports it as *changed* so the pipeline can emit
``DataQualityChanged`` and downstream execution can be gated (SPEC-004 "If readiness falls
below threshold: block live execution").
"""

from __future__ import annotations

from collections import deque

from market_intelligence.domain.quality import (
    ConfidenceLevel,
    QualitySnapshot,
    RejectionReason,
    TradingReadiness,
)
from market_intelligence.ingestion.validator import ValidationOutcome


class DataQualityEngine:
    def __init__(
        self,
        *,
        window_size: int = 100,
        max_drift_ms: int = 5000,
        ready_threshold: float = 0.90,
        degraded_threshold: float = 0.60,
    ) -> None:
        self._window_size = window_size
        self._max_drift_ms = max_drift_ms
        self._ready = ready_threshold
        self._degraded = degraded_threshold
        self._windows: dict[str, deque[ValidationOutcome]] = {}
        self._last_readiness: dict[str, TradingReadiness] = {}

    def observe(self, symbol: str, outcome: ValidationOutcome) -> tuple[QualitySnapshot, bool]:
        window = self._windows.setdefault(symbol, deque(maxlen=self._window_size))
        window.append(outcome)
        snapshot = self._score(symbol, window)
        previous = self._last_readiness.get(symbol)
        changed = previous is None or previous != snapshot.readiness
        self._last_readiness[symbol] = snapshot.readiness
        return snapshot, changed

    def current(self, symbol: str) -> QualitySnapshot | None:
        window = self._windows.get(symbol)
        return self._score(symbol, window) if window else None

    def _score(self, symbol: str, window: deque[ValidationOutcome]) -> QualitySnapshot:
        total = len(window)
        accepted = sum(1 for o in window if o.accepted)
        duplicates = sum(1 for o in window if o.reason is RejectionReason.DUPLICATE)
        gaps_total = sum(o.gap for o in window)
        drift_avg = (sum(o.drift_ms for o in window) / total) if total else 0.0

        acceptance_rate = accepted / total if total else 1.0
        # Fraction of expected packets that were missing within the accepted stream.
        expected = accepted + gaps_total
        gap_rate = (gaps_total / expected) if expected else 0.0
        drift_factor = min(1.0, drift_avg / self._max_drift_ms) if self._max_drift_ms else 0.0

        score = acceptance_rate * (1 - 0.5 * gap_rate) * (1 - 0.3 * drift_factor)
        score = max(0.0, min(1.0, round(score, 4)))

        readiness = (
            TradingReadiness.READY
            if score >= self._ready
            else TradingReadiness.DEGRADED
            if score >= self._degraded
            else TradingReadiness.BLOCKED
        )
        if total < max(1, self._window_size // 4):
            confidence = ConfidenceLevel.LOW
        elif score >= 0.9:
            confidence = ConfidenceLevel.HIGH
        elif score >= 0.7:
            confidence = ConfidenceLevel.MEDIUM
        else:
            confidence = ConfidenceLevel.LOW

        return QualitySnapshot(
            symbol=symbol,
            score=score,
            confidence=confidence,
            readiness=readiness,
            metrics={
                "acceptance_rate": round(acceptance_rate, 4),
                "duplicate_rate": round(duplicates / total, 4) if total else 0.0,
                "gap_rate": round(gap_rate, 4),
                "drift_avg_ms": round(drift_avg, 2),
                "sample_size": float(total),
            },
        )
