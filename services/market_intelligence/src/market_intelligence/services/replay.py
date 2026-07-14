"""Replay engine (SPEC-004 Replay Engine).

Replays the immutable stored ticks for a symbol in deterministic order (by exchange time,
then sequence). Because the store is append-only and the ordering key is total, replaying
the same window always reproduces the identical ``TickReceived`` stream — the property
backtests and audits depend on (SPEC-004 "Replay produces deterministic outputs").

Replay is read-only over the store; it never re-persists ticks. It may optionally
re-publish events (e.g. to drive a downstream consumer through a historical window).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from nexus_shared.events.catalog import EventType
from nexus_shared.events.envelope import EventEnvelope
from nexus_shared.events.publisher import EventPublisher
from nexus_platform.db.session import Database
from market_intelligence.ingestion.pipeline import PRODUCER
from market_intelligence.repositories.market_data import MarketDataRepository


@dataclass(frozen=True, slots=True)
class ReplayReport:
    symbol: str
    replayed: int
    published: bool


class ReplayService:
    def __init__(self, database: Database, publisher: EventPublisher) -> None:
        self._db = database
        self._publisher = publisher

    async def replay_ticks(
        self,
        symbol: str,
        *,
        since: datetime | None = None,
        limit: int = 1000,
        publish: bool = False,
    ) -> ReplayReport:
        async with self._db.session() as session:
            rows = await MarketDataRepository(session).get_ticks(
                symbol, since=since, limit=limit
            )
        if publish:
            for row in rows:
                await self._publisher.publish(
                    EventEnvelope(
                        event_type=EventType.TICK_RECEIVED,
                        producer=PRODUCER,
                        aggregate_id=symbol,
                        payload={
                            "symbol": row.symbol,
                            "exchange": row.exchange,
                            "ltp": row.ltp,
                            "ltq": row.ltq,
                            "volume": row.volume,
                            "sequence": row.sequence,
                            "bid": row.bid,
                            "ask": row.ask,
                            "quality_score": row.quality_score,
                            "exchange_ts": row.exchange_ts.isoformat(),
                        },
                    )
                )
        return ReplayReport(symbol=symbol, replayed=len(rows), published=publish)
