"""Ingestion pipeline orchestrator (SPEC-004 Core Architecture).

Ties the ingestion stages together: for each raw tick it validates, scores quality,
normalises, persists immutably, aggregates candles, and publishes the resulting market
events. A whole batch is persisted in a single transaction; outbound events are published
only after that transaction commits, so the fabric never advertises unpersisted data.

The pipeline holds an in-memory set of known ``(symbol, exchange)`` pairs sourced from the
Instrument Master — an unknown symbol fails validation (SPEC-004 symbol validation) and no
downstream service ingests exchange feeds directly (SPEC-004 Claude Code Contract).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from nexus_shared.events.catalog import EventType
from nexus_shared.events.envelope import EventEnvelope
from nexus_shared.events.publisher import EventPublisher
from nexus_shared.primitives.time import utc_now
from nexus_platform.db.session import Database
from market_intelligence.domain.candles import Candle, Interval
from market_intelligence.domain.quality import QualitySnapshot
from market_intelligence.domain.ticks import NormalizedTick, RawTick
from market_intelligence.ingestion.aggregator import CandleAggregator
from market_intelligence.ingestion.normalizer import Normalizer
from market_intelligence.ingestion.quality import DataQualityEngine
from market_intelligence.ingestion.validator import TickValidator
from market_intelligence.repositories.market_data import MarketDataRepository
from market_intelligence.repositories.quality import DataQualityRepository

PRODUCER = "market_intelligence"


@dataclass
class IngestResult:
    accepted: int = 0
    rejected: int = 0
    candles_closed: int = 0
    quality_changes: int = 0
    events_published: int = 0
    rejections: dict[str, int] = field(default_factory=dict)


class IngestionPipeline:
    def __init__(
        self,
        database: Database,
        publisher: EventPublisher,
        *,
        interval: Interval = Interval.ONE_MINUTE,
        validator: TickValidator | None = None,
        quality: DataQualityEngine | None = None,
    ) -> None:
        self._db = database
        self._publisher = publisher
        self._validator = validator or TickValidator()
        self._quality = quality or DataQualityEngine()
        self._aggregator = CandleAggregator(interval)
        self._known: set[tuple[str, str]] = set()

    def register_symbol(self, symbol: str, exchange: str) -> None:
        self._known.add((symbol, exchange))

    def sync_known_symbols(self, pairs: list[tuple[str, str]]) -> None:
        self._known = set(pairs)

    async def process_batch(self, ticks: list[RawTick]) -> IngestResult:
        result = IngestResult()
        outbound: list[EventEnvelope] = []

        async with self._db.begin() as session:
            market = MarketDataRepository(session)
            dq = DataQualityRepository(session)
            for raw in ticks:
                # Arrival time comes from the collector when provided (replay/simulated
                # feeds carry their own); a live tick without one is arriving now.
                received = raw.received_ts or utc_now()
                known = (raw.symbol, raw.exchange) in self._known
                outcome = self._validator.validate(raw, symbol_known=known, received_ts=received)
                snapshot, changed = self._quality.observe(raw.symbol, outcome)

                if outcome.accepted:
                    result.accepted += 1
                    normalized = Normalizer.normalize(
                        raw, received_ts=received, quality_score=snapshot.score
                    )
                    await market.append_tick(normalized)
                    outbound.append(self._tick_event(normalized))
                    for candle in self._aggregator.add(normalized):
                        await market.append_candle(candle)
                        outbound.append(self._candle_event(candle))
                        result.candles_closed += 1
                else:
                    result.rejected += 1
                    reason = outcome.reason.value if outcome.reason else "unknown"
                    result.rejections[reason] = result.rejections.get(reason, 0) + 1

                if changed:
                    await dq.append(snapshot)
                    outbound.append(self._dq_event(snapshot))
                    result.quality_changes += 1

        await self._publisher.publish_all(outbound)
        result.events_published = len(outbound)
        return result

    async def process_tick(self, raw: RawTick) -> IngestResult:
        return await self.process_batch([raw])

    # --- event builders (SPEC-004 Domain Events) ---

    def _tick_event(self, tick: NormalizedTick) -> EventEnvelope:
        return EventEnvelope(
            event_type=EventType.TICK_RECEIVED,
            producer=PRODUCER,
            aggregate_id=tick.symbol,
            payload={
                "symbol": tick.symbol,
                "exchange": tick.exchange,
                "ltp": tick.ltp,
                "ltq": tick.ltq,
                "volume": tick.volume,
                "sequence": tick.sequence,
                "bid": tick.bid,
                "ask": tick.ask,
                "quality_score": tick.quality_score,
                "exchange_ts": tick.exchange_ts.isoformat(),
            },
        )

    def _candle_event(self, candle: Candle) -> EventEnvelope:
        return EventEnvelope(
            event_type=EventType.CANDLE_CLOSED,
            producer=PRODUCER,
            aggregate_id=candle.symbol,
            payload={
                "symbol": candle.symbol,
                "interval_seconds": int(candle.interval),
                "open_time": candle.open_time.isoformat(),
                "close_time": candle.close_time.isoformat(),
                "open": candle.open,
                "high": candle.high,
                "low": candle.low,
                "close": candle.close,
                "volume": candle.volume,
                "tick_count": candle.tick_count,
            },
        )

    def _dq_event(self, snapshot: QualitySnapshot) -> EventEnvelope:
        return EventEnvelope(
            event_type=EventType.DATA_QUALITY_CHANGED,
            producer=PRODUCER,
            aggregate_id=snapshot.symbol,
            payload={
                "symbol": snapshot.symbol,
                "score": snapshot.score,
                "confidence": snapshot.confidence.value,
                "readiness": snapshot.readiness.value,
                "metrics": snapshot.metrics,
            },
        )
