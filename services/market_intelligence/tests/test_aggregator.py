"""Candle aggregator unit tests: OHLCV correctness and determinism (SPEC-004)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from market_intelligence.domain.candles import Interval
from market_intelligence.domain.ticks import NormalizedTick
from market_intelligence.ingestion.aggregator import CandleAggregator

T0 = datetime(2024, 1, 1, 4, 0, 0, tzinfo=timezone.utc)


def tick(offset_s: int, ltp: float, volume: int, seq: int) -> NormalizedTick:
    ts = T0 + timedelta(seconds=offset_s)
    return NormalizedTick(
        symbol="TCS", exchange="NSE", ltp=ltp, ltq=1, volume=volume,
        sequence=seq, exchange_ts=ts, received_ts=ts, bid=None, ask=None, quality_score=1.0,
    )


def test_ohlcv_within_single_bar() -> None:
    agg = CandleAggregator(Interval.ONE_MINUTE)
    assert agg.add(tick(0, 100.0, 1000, 1)) == []
    assert agg.add(tick(10, 105.0, 1100, 2)) == []
    assert agg.add(tick(20, 95.0, 1300, 3)) == []
    assert agg.add(tick(30, 102.0, 1450, 4)) == []
    candle = agg.flush("TCS")
    assert (candle.open, candle.high, candle.low, candle.close) == (100.0, 105.0, 95.0, 102.0)
    assert candle.volume == 450  # cumulative 1450 - 1000
    assert candle.tick_count == 4


def test_bar_closes_on_bucket_crossing() -> None:
    agg = CandleAggregator(Interval.ONE_MINUTE)
    agg.add(tick(0, 100.0, 1000, 1))
    agg.add(tick(59, 101.0, 1010, 2))
    closed = agg.add(tick(60, 102.0, 1020, 3))  # crosses into the next minute
    assert len(closed) == 1
    assert closed[0].open_time == T0
    assert closed[0].close == 101.0
    # New bar carries the crossing tick.
    next_candle = agg.flush("TCS")
    assert next_candle.open == 102.0


def test_aggregation_is_deterministic() -> None:
    def run() -> list[tuple]:
        agg = CandleAggregator(Interval.ONE_MINUTE)
        out = []
        for i in range(300):
            out.extend(agg.add(tick(i, 100 + (i % 7) * 0.5, 1000 + i * 3, i + 1)))
        return [(c.open_time, c.open, c.high, c.low, c.close, c.volume) for c in out]

    assert run() == run()  # identical input => identical candles (SPEC-004 replay)


def test_symbols_are_independent() -> None:
    agg = CandleAggregator(Interval.ONE_MINUTE)
    a = tick(0, 100.0, 1000, 1)
    b = NormalizedTick(
        symbol="INFY", exchange="NSE", ltp=50.0, ltq=1, volume=500, sequence=1,
        exchange_ts=T0, received_ts=T0, bid=None, ask=None, quality_score=1.0,
    )
    agg.add(a)
    agg.add(b)
    assert agg.flush("TCS").open == 100.0
    assert agg.flush("INFY").open == 50.0
