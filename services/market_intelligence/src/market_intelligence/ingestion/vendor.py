"""Vendor abstraction and a deterministic mock feed (SPEC-004 Vendor abstraction).

Real vendor adapters (Kite, Dhan, exchange multicast) implement :class:`VendorAdapter`.
Per SPEC-001 non-goals (no paid infrastructure during development), the only bundled
adapter is :class:`MockNseVendor`, an explicit development-mode synthetic feed — the one
sanctioned use of generated data. It is a seeded random walk, so a given seed always
produces the identical tick stream (supporting deterministic tests and replay).
"""

from __future__ import annotations

import random
from abc import ABC, abstractmethod
from collections.abc import Iterator
from datetime import datetime, timedelta, timezone

from market_intelligence.domain.ticks import RawTick


class VendorAdapter(ABC):
    """Port for a market-data vendor. Implementations translate a feed into ``RawTick``s."""

    @abstractmethod
    def stream(self, count: int) -> Iterator[RawTick]: ...


class MockNseVendor(VendorAdapter):
    def __init__(
        self,
        symbols: dict[str, float],
        *,
        exchange: str = "NSE",
        seed: int = 42,
        start_ts: datetime | None = None,
        tick_interval_ms: int = 1000,
    ) -> None:
        """``symbols`` maps symbol -> starting price."""
        self._exchange = exchange
        self._rng = random.Random(seed)
        self._prices = dict(symbols)
        self._volumes = {s: 0 for s in symbols}
        self._sequences = {s: 0 for s in symbols}
        self._start_ts = start_ts or datetime(2024, 1, 1, 3, 45, tzinfo=timezone.utc)  # ~09:15 IST
        self._interval = timedelta(milliseconds=tick_interval_ms)

    def stream(self, count: int) -> Iterator[RawTick]:
        symbols = list(self._prices)
        for i in range(count):
            symbol = symbols[i % len(symbols)]
            # Random-walk the price by a small fraction; keep it strictly positive.
            drift = self._rng.uniform(-0.002, 0.002)
            price = max(0.05, round(self._prices[symbol] * (1 + drift), 2))
            self._prices[symbol] = price
            qty = self._rng.randint(1, 500)
            self._volumes[symbol] += qty
            self._sequences[symbol] += 1
            ts = self._start_ts + self._interval * i
            spread = round(price * 0.0005, 2)
            yield RawTick(
                symbol=symbol,
                exchange=self._exchange,
                ltp=price,
                ltq=qty,
                volume=self._volumes[symbol],
                sequence=self._sequences[symbol],
                exchange_ts=ts,
                bid=round(price - spread, 2),
                ask=round(price + spread, 2),
            )
