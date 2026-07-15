"""Market regime classification (SPEC-004 Market Regime Engine).

A pure classifier over a window of closed candles. Trend is derived from the relative
positions of short/long simple moving averages; volatility from the annualised standard
deviation of bar returns. Calendar-driven regimes (expiry week) come from the trading
calendar. The classifier is deterministic: the same candle window always yields the same
regime (SPEC-004 replay determinism).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum


class Regime(str, Enum):
    BULL = "bull"
    BEAR = "bear"
    SIDEWAYS = "sideways"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    EXPIRY_WEEK = "expiry_week"


@dataclass(frozen=True, slots=True)
class RegimeAssessment:
    symbol: str
    trend: Regime
    volatility: Regime | None  # None = normal volatility (no extreme regime)
    tags: list[Regime] = field(default_factory=list)
    indicators: dict[str, float] = field(default_factory=dict)

    @property
    def regimes(self) -> list[Regime]:
        vol = [self.volatility] if self.volatility is not None else []
        return [self.trend, *vol, *self.tags]


class RegimeClassifier:
    def __init__(
        self,
        *,
        short_window: int = 10,
        long_window: int = 30,
        trend_threshold: float = 0.002,
        high_vol_threshold: float = 0.020,
        low_vol_threshold: float = 0.005,
    ) -> None:
        if short_window >= long_window:
            raise ValueError("short_window must be smaller than long_window")
        self._short = short_window
        self._long = long_window
        self._trend_threshold = trend_threshold
        self._high_vol = high_vol_threshold
        self._low_vol = low_vol_threshold

    @property
    def min_bars(self) -> int:
        return self._long

    def classify(
        self, symbol: str, closes: list[float], *, expiry_week: bool = False
    ) -> RegimeAssessment | None:
        """Classify from a chronological list of close prices; None if insufficient data."""
        if len(closes) < self._long:
            return None
        short_ma = sum(closes[-self._short:]) / self._short
        long_ma = sum(closes[-self._long:]) / self._long
        divergence = (short_ma - long_ma) / long_ma

        returns = [
            (closes[i] / closes[i - 1]) - 1.0
            for i in range(len(closes) - self._long + 1, len(closes))
            if closes[i - 1] > 0
        ]
        mean = sum(returns) / len(returns)
        vol = math.sqrt(sum((r - mean) ** 2 for r in returns) / len(returns))

        trend = (
            Regime.BULL
            if divergence > self._trend_threshold
            else Regime.BEAR
            if divergence < -self._trend_threshold
            else Regime.SIDEWAYS
        )
        volatility: Regime | None = (
            Regime.HIGH_VOLATILITY
            if vol > self._high_vol
            else Regime.LOW_VOLATILITY
            if vol < self._low_vol
            else None  # normal volatility: no extreme regime
        )
        tags = [Regime.EXPIRY_WEEK] if expiry_week else []
        return RegimeAssessment(
            symbol=symbol,
            trend=trend,
            volatility=volatility,
            tags=tags,
            indicators={
                "short_ma": round(short_ma, 4),
                "long_ma": round(long_ma, 4),
                "ma_divergence": round(divergence, 6),
                "volatility": round(vol, 6),
            },
        )
