"""Read queries for market data (SPEC-004 Public APIs)."""

from __future__ import annotations

from datetime import datetime

from nexus_platform.db.session import Database
from market_intelligence.domain.candles import Interval
from market_intelligence.repositories.market_data import MarketDataRepository
from market_intelligence.repositories.quality import DataQualityRepository


class MarketQueryService:
    def __init__(self, database: Database) -> None:
        self._db = database

    async def ticks(self, symbol: str, *, since: datetime | None = None, limit: int = 500) -> list[dict]:
        async with self._db.session() as session:
            rows = await MarketDataRepository(session).get_ticks(symbol, since=since, limit=limit)
        return [
            {
                "symbol": r.symbol,
                "exchange": r.exchange,
                "ltp": r.ltp,
                "ltq": r.ltq,
                "volume": r.volume,
                "sequence": r.sequence,
                "bid": r.bid,
                "ask": r.ask,
                "quality_score": r.quality_score,
                "exchange_ts": r.exchange_ts.isoformat(),
            }
            for r in rows
        ]

    async def candles(
        self, symbol: str, interval: Interval, *, since: datetime | None = None, limit: int = 500
    ) -> list[dict]:
        async with self._db.session() as session:
            rows = await MarketDataRepository(session).get_candles(
                symbol, interval, since=since, limit=limit
            )
        return [
            {
                "symbol": r.symbol,
                "interval_seconds": r.interval_seconds,
                "open_time": r.open_time.isoformat(),
                "close_time": r.close_time.isoformat(),
                "open": r.open,
                "high": r.high,
                "low": r.low,
                "close": r.close,
                "volume": r.volume,
                "tick_count": r.tick_count,
            }
            for r in rows
        ]

    async def quality(self, symbol: str) -> dict | None:
        async with self._db.session() as session:
            row = await DataQualityRepository(session).latest(symbol)
        if row is None:
            return None
        return {
            "symbol": row.symbol,
            "score": row.score,
            "confidence": row.confidence,
            "readiness": row.readiness,
            "metrics": row.metrics,
            "as_of": row.created_at.isoformat(),
        }
