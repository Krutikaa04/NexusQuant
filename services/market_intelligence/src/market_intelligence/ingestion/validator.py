"""Tick validation (SPEC-004 tick validation <5 ms; Data Quality metrics).

The validator is a pure, in-memory state machine keyed by symbol. It classifies each tick
and surfaces the quality signals the Data Quality Engine aggregates: duplicates, sequence
gaps (missing packets), out-of-order delivery, timestamp drift, and price sanity.

Rejections are terminal for a tick (duplicate, non-monotonic, unknown symbol, invalid
price, excessive drift). A *gap* is not a rejection — the tick is accepted but the number
of skipped sequences is reported so downstream can score feed completeness.
"""

from __future__ import annotations

from dataclasses import dataclass

from market_intelligence.domain.quality import RejectionReason
from market_intelligence.domain.ticks import RawTick


@dataclass(frozen=True, slots=True)
class ValidationOutcome:
    accepted: bool
    reason: RejectionReason | None = None
    gap: int = 0  # number of missed sequence numbers immediately before this tick
    drift_ms: float = 0.0


class TickValidator:
    def __init__(self, *, max_drift_ms: int = 5000) -> None:
        self._max_drift_ms = max_drift_ms
        self._last_sequence: dict[str, int] = {}

    def validate(
        self, tick: RawTick, *, symbol_known: bool, received_ts
    ) -> ValidationOutcome:
        if not symbol_known:
            return ValidationOutcome(False, RejectionReason.UNKNOWN_SYMBOL)
        if tick.ltp <= 0 or tick.ltq < 0:
            return ValidationOutcome(False, RejectionReason.INVALID_PRICE)

        drift_ms = abs((received_ts - tick.exchange_ts).total_seconds()) * 1000.0
        if drift_ms > self._max_drift_ms:
            return ValidationOutcome(False, RejectionReason.TIMESTAMP_DRIFT, drift_ms=drift_ms)

        last = self._last_sequence.get(tick.symbol)
        if last is not None:
            if tick.sequence == last:
                return ValidationOutcome(False, RejectionReason.DUPLICATE, drift_ms=drift_ms)
            if tick.sequence < last:
                return ValidationOutcome(False, RejectionReason.NON_MONOTONIC, drift_ms=drift_ms)

        gap = 0 if last is None else max(0, tick.sequence - last - 1)
        self._last_sequence[tick.symbol] = tick.sequence
        return ValidationOutcome(True, None, gap=gap, drift_ms=drift_ms)
