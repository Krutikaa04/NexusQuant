"""Tick normalisation (SPEC-004 Normalizer stage).

Turns a validated :class:`RawTick` into an immutable :class:`NormalizedTick`, stamping the
receive time and the current quality score. Kept deliberately small and pure; venue-specific
canonicalisation (symbol remaps, price scaling) would extend here.
"""

from __future__ import annotations

from datetime import datetime

from market_intelligence.domain.ticks import NormalizedTick, RawTick


class Normalizer:
    @staticmethod
    def normalize(tick: RawTick, *, received_ts: datetime, quality_score: float) -> NormalizedTick:
        return NormalizedTick(
            symbol=tick.symbol,
            exchange=tick.exchange,
            ltp=tick.ltp,
            ltq=tick.ltq,
            volume=tick.volume,
            sequence=tick.sequence,
            exchange_ts=tick.exchange_ts,
            received_ts=received_ts,
            bid=tick.bid,
            ask=tick.ask,
            quality_score=quality_score,
        )
