"""Ingestion pipeline integration tests: persist, aggregate, publish (SPEC-004)."""

from __future__ import annotations

from nexus_shared.events.catalog import EventType
from market_intelligence.domain.candles import Interval
from market_intelligence.ingestion.vendor import MockNseVendor
from market_intelligence.repositories.market_data import MarketDataRepository


async def seed_instrument(container, instrument, symbol: str = "RELIANCE") -> None:
    await container.instruments.upsert(instrument(symbol))


async def test_full_pipeline_persists_and_publishes(container, publisher, instrument) -> None:
    await seed_instrument(container, instrument)
    vendor = MockNseVendor({"RELIANCE": 2950.0}, seed=7)
    result = await container.pipeline.process_batch(list(vendor.stream(120)))

    assert result.accepted == 120
    assert result.rejected == 0
    assert result.candles_closed >= 1  # 120 ticks at 1s intervals crosses minute bars

    async with container.database.session() as session:
        repo = MarketDataRepository(session)
        ticks = await repo.get_ticks("RELIANCE", limit=1000)
        candles = await repo.get_candles("RELIANCE", Interval.ONE_MINUTE, limit=100)
    assert len(ticks) == 120
    assert len(candles) == result.candles_closed

    assert len(publisher.of_type(EventType.TICK_RECEIVED)) == 120
    assert len(publisher.of_type(EventType.CANDLE_CLOSED)) == result.candles_closed
    assert len(publisher.of_type(EventType.DATA_QUALITY_CHANGED)) >= 1


async def test_unknown_symbol_is_rejected_not_persisted(container, publisher) -> None:
    vendor = MockNseVendor({"GHOST": 100.0})
    result = await container.pipeline.process_batch(list(vendor.stream(10)))
    assert result.accepted == 0
    assert result.rejections.get("unknown_symbol") == 10
    async with container.database.session() as session:
        assert await MarketDataRepository(session).get_ticks("GHOST") == []
    assert publisher.of_type(EventType.TICK_RECEIVED) == []


async def test_candle_ohlc_consistency(container, publisher, instrument) -> None:
    await seed_instrument(container, instrument, "TCS")
    vendor = MockNseVendor({"TCS": 3900.0}, seed=11)
    await container.pipeline.process_batch(list(vendor.stream(180)))
    async with container.database.session() as session:
        candles = await MarketDataRepository(session).get_candles(
            "TCS", Interval.ONE_MINUTE, limit=100
        )
    for c in candles:
        assert c.low <= c.open <= c.high
        assert c.low <= c.close <= c.high
        assert c.tick_count > 0


async def test_replay_returns_stored_ticks_deterministically(
    container, publisher, instrument
) -> None:
    await seed_instrument(container, instrument)
    vendor = MockNseVendor({"RELIANCE": 2950.0}, seed=3)
    await container.pipeline.process_batch(list(vendor.stream(50)))

    first = await container.replay.replay_ticks("RELIANCE", limit=100)
    second = await container.replay.replay_ticks("RELIANCE", limit=100)
    assert first.replayed == second.replayed == 50

    before = len(publisher.of_type(EventType.TICK_RECEIVED))
    report = await container.replay.replay_ticks("RELIANCE", limit=100, publish=True)
    after = len(publisher.of_type(EventType.TICK_RECEIVED))
    assert report.published and after - before == 50


async def test_instrument_versioning_and_event(container, publisher, instrument) -> None:
    rev1 = await container.instruments.upsert(instrument("INFY"))
    rev2 = await container.instruments.upsert(instrument("INFY", sector="IT"))
    assert (rev1, rev2) == (1, 2)
    current = await container.instruments.get("INFY", instrument("INFY").exchange)
    assert current.sector == "IT"
    events = publisher.of_type(EventType.INSTRUMENT_UPDATED)
    assert [e.payload["revision"] for e in events] == [1, 2]
