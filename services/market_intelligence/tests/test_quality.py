"""Data Quality Engine unit tests (SPEC-004 Data Quality Engine)."""

from __future__ import annotations

from market_intelligence.domain.quality import RejectionReason, TradingReadiness
from market_intelligence.ingestion.quality import DataQualityEngine
from market_intelligence.ingestion.validator import ValidationOutcome

OK = ValidationOutcome(True)
DUP = ValidationOutcome(False, RejectionReason.DUPLICATE)


def test_clean_stream_is_ready() -> None:
    engine = DataQualityEngine(window_size=20)
    snapshot = None
    for _ in range(20):
        snapshot, _ = engine.observe("RELIANCE", OK)
    assert snapshot.score >= 0.99
    assert snapshot.readiness is TradingReadiness.READY


def test_degradation_flips_readiness_and_reports_change() -> None:
    engine = DataQualityEngine(window_size=10, ready_threshold=0.9, degraded_threshold=0.5)
    changes = 0
    for _ in range(10):
        _, changed = engine.observe("X", OK)
        changes += changed
    assert changes == 1  # initial READY transition only
    # Flood with duplicates until readiness degrades.
    flipped = False
    for _ in range(10):
        snapshot, changed = engine.observe("X", DUP)
        if changed:
            flipped = True
            assert snapshot.readiness in (TradingReadiness.DEGRADED, TradingReadiness.BLOCKED)
    assert flipped


def test_gaps_reduce_score() -> None:
    engine = DataQualityEngine(window_size=10)
    clean, _ = engine.observe("A", OK)
    gappy = DataQualityEngine(window_size=10)
    snapshot = None
    for _ in range(5):
        snapshot, _ = gappy.observe("B", ValidationOutcome(True, gap=3))
    assert snapshot.score < clean.score


def test_current_returns_latest_snapshot() -> None:
    engine = DataQualityEngine(window_size=5)
    assert engine.current("NOPE") is None
    engine.observe("Y", OK)
    assert engine.current("Y").symbol == "Y"
