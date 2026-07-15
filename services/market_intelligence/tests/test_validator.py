"""Tick validator unit tests (SPEC-004 tick validation; chaos scenarios)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from market_intelligence.domain.quality import RejectionReason
from market_intelligence.domain.ticks import RawTick
from market_intelligence.ingestion.validator import TickValidator

NOW = datetime(2024, 1, 1, 4, 0, tzinfo=timezone.utc)


def tick(sequence: int, *, ltp: float = 100.0, ts: datetime = NOW, ltq: int = 10) -> RawTick:
    return RawTick(
        symbol="RELIANCE", exchange="NSE", ltp=ltp, ltq=ltq, volume=1000,
        sequence=sequence, exchange_ts=ts,
    )


def test_accepts_valid_monotonic_ticks() -> None:
    v = TickValidator()
    assert v.validate(tick(1), symbol_known=True, received_ts=NOW).accepted
    assert v.validate(tick(2), symbol_known=True, received_ts=NOW).accepted


def test_rejects_unknown_symbol() -> None:
    v = TickValidator()
    outcome = v.validate(tick(1), symbol_known=False, received_ts=NOW)
    assert not outcome.accepted
    assert outcome.reason is RejectionReason.UNKNOWN_SYMBOL


def test_rejects_duplicate_sequence() -> None:
    v = TickValidator()
    v.validate(tick(5), symbol_known=True, received_ts=NOW)
    outcome = v.validate(tick(5), symbol_known=True, received_ts=NOW)
    assert outcome.reason is RejectionReason.DUPLICATE


def test_rejects_out_of_order_sequence() -> None:
    v = TickValidator()
    v.validate(tick(5), symbol_known=True, received_ts=NOW)
    outcome = v.validate(tick(3), symbol_known=True, received_ts=NOW)
    assert outcome.reason is RejectionReason.NON_MONOTONIC


def test_reports_sequence_gap_without_rejecting() -> None:
    v = TickValidator()
    v.validate(tick(1), symbol_known=True, received_ts=NOW)
    outcome = v.validate(tick(5), symbol_known=True, received_ts=NOW)
    assert outcome.accepted
    assert outcome.gap == 3  # sequences 2,3,4 missing


def test_rejects_excessive_timestamp_drift() -> None:
    v = TickValidator(max_drift_ms=1000)
    stale = tick(1, ts=NOW - timedelta(seconds=5))
    outcome = v.validate(stale, symbol_known=True, received_ts=NOW)
    assert outcome.reason is RejectionReason.TIMESTAMP_DRIFT


def test_rejects_invalid_price() -> None:
    v = TickValidator()
    outcome = v.validate(tick(1, ltp=0.0), symbol_known=True, received_ts=NOW)
    assert outcome.reason is RejectionReason.INVALID_PRICE
