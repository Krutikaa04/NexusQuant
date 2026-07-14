"""Candle aggregation (SPEC-004 candle aggregation).

Maintains one in-progress OHLCV bar per (symbol, interval). Feeding a tick either updates
the current bar or — when the tick crosses into a new time bucket — *closes* the current
bar and opens a fresh one. Closing is deterministic: identical tick input always yields
identical candles (SPEC-004 replay determinism).

Volume is treated as the exchange's cumulative day volume, so per-bar volume is the delta
between the last and first cumulative reading observed within the bar.
"""

from __future__ import annotations

from dataclasses import dataclass

from market_intelligence.domain.candles import Candle, Interval
from market_intelligence.domain.ticks import NormalizedTick


@dataclass
class _Builder:
    open_time: object
    open: float
    high: float
    low: float
    close: float
    first_cum_volume: int
    last_cum_volume: int
    tick_count: int


class CandleAggregator:
    def __init__(self, interval: Interval = Interval.ONE_MINUTE) -> None:
        self._interval = interval
        self._builders: dict[str, _Builder] = {}

    def add(self, tick: NormalizedTick) -> list[Candle]:
        """Feed a tick; return any candles that closed as a result (usually 0 or 1)."""
        closed: list[Candle] = []
        bucket = self._interval.bucket_start(tick.exchange_ts)
        builder = self._builders.get(tick.symbol)

        if builder is not None and bucket > builder.open_time:
            closed.append(self._finalise(tick.symbol, builder))
            builder = None

        if builder is None:
            self._builders[tick.symbol] = _Builder(
                open_time=bucket,
                open=tick.ltp,
                high=tick.ltp,
                low=tick.ltp,
                close=tick.ltp,
                first_cum_volume=tick.volume,
                last_cum_volume=tick.volume,
                tick_count=1,
            )
        else:
            builder.high = max(builder.high, tick.ltp)
            builder.low = min(builder.low, tick.ltp)
            builder.close = tick.ltp
            builder.last_cum_volume = tick.volume
            builder.tick_count += 1

        return closed

    def flush(self, symbol: str) -> Candle | None:
        """Close the open bar for a symbol (e.g. at session end)."""
        builder = self._builders.pop(symbol, None)
        return self._finalise(symbol, builder, keep=False) if builder else None

    def _finalise(self, symbol: str, builder: _Builder, *, keep: bool = True) -> Candle:
        from datetime import timedelta

        close_time = builder.open_time + timedelta(seconds=int(self._interval))
        candle = Candle(
            symbol=symbol,
            interval=self._interval,
            open_time=builder.open_time,
            close_time=close_time,
            open=builder.open,
            high=builder.high,
            low=builder.low,
            close=builder.close,
            volume=max(0, builder.last_cum_volume - builder.first_cum_volume),
            tick_count=builder.tick_count,
        )
        if keep:
            self._builders.pop(symbol, None)
        return candle
