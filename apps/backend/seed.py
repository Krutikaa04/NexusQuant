"""Development seeding + a gentle live feed for the demo backend.

Everything the UI shows is produced by the *real* SPEC-004 pipeline: we register a small
NSE instrument universe, then push synthetic ticks through the actual ingestion pipeline
(validation → quality → candles → events). No dashboard number is fabricated — each is a
query result over data the pipeline persisted.
"""

from __future__ import annotations

import asyncio
import logging

from market_intelligence.container import Container
from market_intelligence.domain.candles import Interval
from market_intelligence.domain.instruments import Exchange, Instrument, Segment
from market_intelligence.domain.regime import RegimeClassifier
from market_intelligence.ingestion.vendor import MockNseVendor
from market_intelligence.services.reference import RegimeService

logger = logging.getLogger("nexus.backend.seed")

# (symbol, name, segment, base_price, sector, industry)
UNIVERSE: list[tuple[str, str, Segment, float, str | None, str | None]] = [
    ("RELIANCE", "Reliance Industries", Segment.EQUITY, 2950.0, "Energy", "Refineries"),
    ("TCS", "Tata Consultancy Services", Segment.EQUITY, 3900.0, "IT", "Software"),
    ("INFY", "Infosys", Segment.EQUITY, 1500.0, "IT", "Software"),
    ("HDFCBANK", "HDFC Bank", Segment.EQUITY, 1650.0, "Financials", "Private Bank"),
    ("ICICIBANK", "ICICI Bank", Segment.EQUITY, 1150.0, "Financials", "Private Bank"),
    ("SBIN", "State Bank of India", Segment.EQUITY, 820.0, "Financials", "Public Bank"),
    ("BHARTIARTL", "Bharti Airtel", Segment.EQUITY, 1500.0, "Telecom", "Telecom Services"),
    ("ITC", "ITC", Segment.EQUITY, 440.0, "FMCG", "Diversified"),
    ("NIFTY50", "NIFTY 50", Segment.INDEX, 24500.0, "Index", "Broad Market"),
    ("NIFTYBANK", "NIFTY Bank", Segment.INDEX, 51000.0, "Index", "Banking"),
    ("NIFTYIT", "NIFTY IT", Segment.INDEX, 43000.0, "Index", "Technology"),
]

EQUITY_TICKS = 1000  # ~16 one-minute candles: enough for the (tuned) regime classifier
INDEX_TICKS = 700


def use_demo_regime_classifier(container: Container) -> None:
    """Swap in a shorter-window regime classifier so the seeded window is classifiable."""
    container.regime = RegimeService(
        container.database,
        container.publisher,
        container.calendar,
        classifier=RegimeClassifier(short_window=5, long_window=12),
        interval=Interval.ONE_MINUTE,
    )


def base_prices() -> dict[str, float]:
    return {row[0]: row[3] for row in UNIVERSE}


async def already_seeded(container: Container) -> bool:
    return len(await container.instruments.list()) > 0


async def seed(container: Container, *, backfill: bool = True) -> None:
    """Register the universe and (optionally) backfill synthetic history.

    Idempotent: skips if already seeded. ``backfill=False`` registers instruments only and
    generates NO synthetic ticks — used when a real market-data provider is connected, so
    real quotes are never mixed with fabricated history.
    """
    if await already_seeded(container):
        logger.info("universe already seeded; skipping backfill")
        return

    logger.info("seeding instrument universe (%d symbols)…", len(UNIVERSE))
    for symbol, name, segment, _price, sector, industry in UNIVERSE:
        await container.instruments.upsert(
            Instrument(
                symbol=symbol,
                exchange=Exchange.NSE,
                name=name,
                segment=segment,
                sector=sector,
                industry=industry,
            )
        )

    if not backfill:
        logger.info("real provider connected — skipping synthetic backfill")
        return

    for i, (symbol, _n, segment, price, *_rest) in enumerate(UNIVERSE):
        count = INDEX_TICKS if segment is Segment.INDEX else EQUITY_TICKS
        vendor = MockNseVendor({symbol: price}, seed=17 + i * 7)
        await container.pipeline.process_batch(list(vendor.stream(count)))

    for symbol, *_ in UNIVERSE:
        await container.regime.assess(symbol)
    logger.info("backfill complete")


class LiveFeed:
    """A background task pushing a trickle of ticks so the UI feels live.

    It continues each symbol's price from where the backfill left off, emitting one tick
    per symbol per cycle through the real pipeline — the same events the WebSocket streams.
    """

    def __init__(self, container: Container, *, interval_s: float = 1.5) -> None:
        self._container = container
        self._interval = interval_s
        self._task: asyncio.Task | None = None
        self._vendor: MockNseVendor | None = None

    async def start(self) -> None:
        prices = await self._current_prices()
        # Continue each symbol's sequence and the time axis from where the backfill (or a
        # previous run against the persisted DB) ended, so live ticks are strictly
        # monotonic (never rejected as out-of-order) and new candles land in fresh buckets.
        sequences, start_ts = await self._continuation()
        self._vendor = MockNseVendor(prices, seed=99, tick_interval_ms=1000, start_ts=start_ts)
        self._vendor._sequences = sequences  # harness continuation of the mock feed state
        self._task = asyncio.create_task(self._run(), name="nexus-live-feed")
        logger.info("live feed started (%d symbols)", len(prices))

    async def _current_prices(self) -> dict[str, float]:
        prices = base_prices()
        for symbol in list(prices):
            candles = await self._container.queries.candles(
                symbol, Interval.ONE_MINUTE, limit=1
            )
            if candles:
                prices[symbol] = candles[-1]["close"]
        return prices

    async def _continuation(self):
        """Return (per-symbol last sequence, next start timestamp) after stored history."""
        from datetime import datetime, timedelta, timezone

        from sqlalchemy import func, select

        from market_intelligence.db.models import CandleRecord, TickRecord

        sequences: dict[str, int] = {}
        async with self._container.database.session() as session:
            for symbol in base_prices():
                mx = (
                    await session.execute(
                        select(func.max(TickRecord.sequence)).where(TickRecord.symbol == symbol)
                    )
                ).scalar_one_or_none()
                sequences[symbol] = mx or 0
            last_close = (
                await session.execute(select(func.max(CandleRecord.close_time)))
            ).scalar_one_or_none()

        if last_close is None:
            start_ts = datetime(2024, 1, 1, 4, 0, tzinfo=timezone.utc)
        else:
            if last_close.tzinfo is None:
                last_close = last_close.replace(tzinfo=timezone.utc)
            start_ts = last_close + timedelta(seconds=120)
        return sequences, start_ts

    async def _run(self) -> None:
        from datetime import timedelta

        assert self._vendor is not None
        n = len(base_prices())
        while True:
            await asyncio.sleep(self._interval)
            try:
                # March the time axis forward each cycle so timestamps never repeat
                # (the mock vendor keys timestamps off a per-call index) — this lets
                # candles advance and avoids bucket collisions.
                self._vendor._start_ts += timedelta(seconds=n)
                batch = list(self._vendor.stream(n))
                await self._container.pipeline.process_batch(batch)
            except asyncio.CancelledError:  # graceful shutdown
                raise
            except Exception:  # never let one bad cycle take the feed down
                logger.exception("live feed cycle failed; continuing")

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
