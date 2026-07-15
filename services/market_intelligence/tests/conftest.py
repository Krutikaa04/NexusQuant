"""Test fixtures: isolated in-memory DB and a capturing event publisher."""

from __future__ import annotations

import pytest
import pytest_asyncio

from nexus_shared.events.publisher import InMemoryEventPublisher
from market_intelligence.config import Settings
from market_intelligence.container import Container
from market_intelligence.domain.instruments import Exchange, Instrument, Segment


@pytest.fixture
def settings() -> Settings:
    return Settings(
        MARKET_DATABASE_URL="sqlite+aiosqlite:///:memory:",
        auth_enabled=False,
        dq_window_size=50,
    )


@pytest.fixture
def publisher() -> InMemoryEventPublisher:
    return InMemoryEventPublisher()


@pytest_asyncio.fixture
async def container(settings, publisher) -> Container:
    c = Container.build(settings, publisher=publisher)
    await c.startup()
    try:
        yield c
    finally:
        await c.shutdown()


def make_instrument(symbol: str = "RELIANCE", **overrides) -> Instrument:
    fields = dict(
        symbol=symbol,
        exchange=Exchange.NSE,
        name=f"{symbol} Ltd",
        segment=Segment.EQUITY,
        isin="INE002A01018",
        sector="Energy",
        industry="Refineries",
    )
    fields.update(overrides)
    return Instrument(**fields)


@pytest.fixture
def instrument():
    return make_instrument
