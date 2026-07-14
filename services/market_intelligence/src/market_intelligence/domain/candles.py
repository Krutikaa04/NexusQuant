"""Candle (OHLCV bar) domain types (SPEC-004 candle aggregation)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import IntEnum


class Interval(IntEnum):
    """Candle interval expressed in seconds — the value is the bar width."""

    ONE_MINUTE = 60
    FIVE_MINUTE = 300
    FIFTEEN_MINUTE = 900
    ONE_HOUR = 3600
    ONE_DAY = 86_400

    def bucket_start(self, moment: datetime) -> datetime:
        """The inclusive start of the bar that ``moment`` falls into (UTC-aligned)."""
        epoch = int(moment.replace(tzinfo=moment.tzinfo or timezone.utc).timestamp())
        start = epoch - (epoch % int(self))
        return datetime.fromtimestamp(start, tz=timezone.utc)


@dataclass(frozen=True, slots=True)
class Candle:
    """An immutable OHLCV bar for one instrument and interval (SPEC-004)."""

    symbol: str
    interval: Interval
    open_time: datetime
    close_time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    tick_count: int
