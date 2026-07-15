"""Market regime classification tests (SPEC-004 Market Regime Engine)."""

from __future__ import annotations

from nexus_shared.events.catalog import EventType
from market_intelligence.domain.regime import Regime, RegimeClassifier
from market_intelligence.ingestion.vendor import MockNseVendor

CLASSIFIER = RegimeClassifier(short_window=5, long_window=15)


def test_insufficient_data_returns_none() -> None:
    assert CLASSIFIER.classify("X", [100.0] * 10) is None


def test_rising_prices_classify_bull() -> None:
    closes = [100.0 * (1.01**i) for i in range(30)]
    assessment = CLASSIFIER.classify("X", closes)
    assert assessment.trend is Regime.BULL


def test_falling_prices_classify_bear() -> None:
    closes = [100.0 * (0.99**i) for i in range(30)]
    assert CLASSIFIER.classify("X", closes).trend is Regime.BEAR


def test_flat_prices_classify_sideways_low_vol() -> None:
    closes = [100.0 + (0.01 if i % 2 else -0.01) for i in range(30)]
    assessment = CLASSIFIER.classify("X", closes)
    assert assessment.trend is Regime.SIDEWAYS
    assert assessment.volatility is Regime.LOW_VOLATILITY


def test_wild_swings_classify_high_volatility() -> None:
    closes = [100.0 * (1.05 if i % 2 else 0.95) ** 1 for i in range(30)]
    assessment = CLASSIFIER.classify("X", closes)
    assert assessment.volatility is Regime.HIGH_VOLATILITY


def test_expiry_week_tag() -> None:
    closes = [100.0] * 30
    assessment = CLASSIFIER.classify("X", closes, expiry_week=True)
    assert Regime.EXPIRY_WEEK in assessment.regimes


def test_classification_is_deterministic() -> None:
    closes = [100.0 + (i % 9) * 0.7 for i in range(40)]
    a = CLASSIFIER.classify("X", closes)
    b = CLASSIFIER.classify("X", closes)
    assert a.regimes == b.regimes
    assert a.indicators == b.indicators


async def test_regime_service_end_to_end(container, publisher, instrument) -> None:
    """Ingest ticks -> candles -> assess regime -> snapshot persisted + event published."""
    await container.instruments.upsert(instrument("RELIANCE"))
    vendor = MockNseVendor({"RELIANCE": 2950.0}, seed=5)
    # 40 minutes of 1s ticks => ~40 one-minute candles, enough for the default classifier.
    await container.pipeline.process_batch(list(vendor.stream(2400)))

    result = await container.regime.assess("RELIANCE")
    assert result is not None and result["changed"] is True
    assert result["regimes"]  # at least a trend regime

    current = await container.regime.current("RELIANCE")
    assert current["regimes"] == result["regimes"]

    events = publisher.of_type(EventType.MARKET_REGIME_CHANGED)
    assert len(events) == 1

    # Re-assessing an unchanged market publishes nothing new.
    again = await container.regime.assess("RELIANCE")
    assert again["changed"] is False
    assert len(publisher.of_type(EventType.MARKET_REGIME_CHANGED)) == 1
