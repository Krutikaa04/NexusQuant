"""Immutable tick and candle store (SPEC-004 Market Intelligence Store)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select

from nexus_platform.db.repository import BaseRepository
from market_intelligence.db.models import CandleRecord, TickRecord
from market_intelligence.domain.candles import Candle, Interval
from market_intelligence.domain.ticks import NormalizedTick


class MarketDataRepository(BaseRepository[TickRecord]):
    model = TickRecord

    async def append_tick(self, tick: NormalizedTick) -> None:
        self.session.add(
            TickRecord(
                symbol=tick.symbol,
                exchange=tick.exchange,
                ltp=tick.ltp,
                ltq=tick.ltq,
                volume=tick.volume,
                sequence=tick.sequence,
                bid=tick.bid,
                ask=tick.ask,
                quality_score=tick.quality_score,
                exchange_ts=tick.exchange_ts,
                received_ts=tick.received_ts,
            )
        )

    async def append_candle(self, candle: Candle) -> None:
        self.session.add(
            CandleRecord(
                symbol=candle.symbol,
                interval_seconds=int(candle.interval),
                open_time=candle.open_time,
                close_time=candle.close_time,
                open=candle.open,
                high=candle.high,
                low=candle.low,
                close=candle.close,
                volume=candle.volume,
                tick_count=candle.tick_count,
            )
        )

    async def get_ticks(
        self, symbol: str, *, since: datetime | None = None, limit: int = 500
    ) -> list[TickRecord]:
        stmt = select(TickRecord).where(TickRecord.symbol == symbol)
        if since is not None:
            stmt = stmt.where(TickRecord.exchange_ts >= since)
        stmt = stmt.order_by(TickRecord.exchange_ts.asc(), TickRecord.sequence.asc()).limit(limit)
        return list((await self.session.execute(stmt)).scalars().all())

    async def get_candles(
        self,
        symbol: str,
        interval: Interval,
        *,
        since: datetime | None = None,
        limit: int = 500,
    ) -> list[CandleRecord]:
        stmt = select(CandleRecord).where(
            CandleRecord.symbol == symbol,
            CandleRecord.interval_seconds == int(interval),
        )
        if since is not None:
            stmt = stmt.where(CandleRecord.open_time >= since)
        stmt = stmt.order_by(CandleRecord.open_time.asc()).limit(limit)
        return list((await self.session.execute(stmt)).scalars().all())
