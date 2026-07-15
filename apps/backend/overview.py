"""Dashboard aggregation for the frontend (a backend-for-frontend read layer).

Assembles the Market Intelligence dashboard payload from the real service queries so the UI
makes one call instead of N. Every field is derived from persisted pipeline output:
last/first candle for price + change, the quality engine for readiness, the regime engine
for market state, the calendar for session phase.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select

from market_intelligence.container import Container
from market_intelligence.db.models import TickRecord
from market_intelligence.domain.calendar import IST
from market_intelligence.domain.candles import Interval

from seed import UNIVERSE


async def _latest_price(container: Container, symbol: str) -> float | None:
    """Most recent tick price for a symbol — the live last-traded price."""
    async with container.database.session() as session:
        row = (
            await session.execute(
                select(TickRecord.ltp)
                .where(TickRecord.symbol == symbol)
                .order_by(TickRecord.sequence.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
    return row


def _meta(symbol: str) -> tuple[str, str, str]:
    for sym, name, segment, _p, sector, _ind in UNIVERSE:
        if sym == symbol:
            return name, segment.value, sector or "—"
    return symbol, "EQ", "—"


async def _instrument_snapshot(container: Container, symbol: str) -> dict:
    name, segment, sector = _meta(symbol)
    candles = await container.queries.candles(symbol, Interval.ONE_MINUTE, limit=240)
    quality = await container.queries.quality(symbol)
    regime = await container.regime.current(symbol)

    # Live last-traded price from the most recent tick; fall back to last candle close.
    last = await _latest_price(container, symbol)
    if last is None:
        last = candles[-1]["close"] if candles else None
    first = candles[0]["open"] if candles else None
    change_pct = ((last - first) / first * 100.0) if (last and first) else 0.0
    spark = [round(c["close"], 2) for c in candles[-60:]]
    day_high = max([c["high"] for c in candles] + ([last] if last else []), default=last)
    day_low = min([c["low"] for c in candles] + ([last] if last else []), default=last)

    return {
        "symbol": symbol,
        "name": name,
        "segment": segment,
        "sector": sector,
        "last": round(last, 2) if last is not None else None,
        "change_pct": round(change_pct, 2),
        "day_high": round(day_high, 2) if day_high is not None else None,
        "day_low": round(day_low, 2) if day_low is not None else None,
        "spark": spark,
        "readiness": quality["readiness"] if quality else "unknown",
        "quality_score": quality["score"] if quality else None,
        "regimes": regime["regimes"] if regime else [],
        "candle_count": len(candles),
    }


async def build_overview(container: Container) -> dict:
    instruments = await container.instruments.list()
    snapshots = [await _instrument_snapshot(container, i.symbol) for i in instruments]

    equities = [s for s in snapshots if s["segment"] != "INDEX"]
    indices = [s for s in snapshots if s["segment"] == "INDEX"]

    ranked = sorted(
        (s for s in equities if s["last"] is not None),
        key=lambda s: s["change_pct"],
        reverse=True,
    )
    advances = sum(1 for s in equities if s["change_pct"] > 0)
    declines = sum(1 for s in equities if s["change_pct"] < 0)
    unchanged = len(equities) - advances - declines

    now = datetime.now(IST)
    calendar = await container.calendar.load()
    window = calendar.session_window(now.date())

    ready = sum(1 for s in snapshots if s["readiness"] == "ready")
    avg_quality = (
        round(sum(s["quality_score"] or 0 for s in snapshots) / len(snapshots), 4)
        if snapshots
        else 0.0
    )

    return {
        "as_of": now.isoformat(),
        "session": {
            "exchange": "NSE",
            "phase": calendar.phase_at(now).value,
            "is_trading_day": calendar.is_trading_day(now.date()),
            "is_holiday": calendar.is_holiday(now.date()),
            "open": window[0].isoformat() if window else None,
            "close": window[1].isoformat() if window else None,
        },
        "breadth": {
            "advances": advances,
            "declines": declines,
            "unchanged": unchanged,
            "total": len(equities),
        },
        "quality": {
            "ready": ready,
            "total": len(snapshots),
            "avg_score": avg_quality,
        },
        "indices": indices,
        "equities": equities,
        "gainers": ranked[:5],
        "losers": list(reversed(ranked[-5:])) if len(ranked) >= 5 else list(reversed(ranked)),
    }
