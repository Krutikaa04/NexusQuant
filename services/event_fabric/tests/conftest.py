"""Shared test fixtures. Every test runs against a fresh in-memory SQLite database and a
private schema registry, so tests are hermetic and require no external infrastructure."""

from __future__ import annotations

import pytest
import pytest_asyncio
from pydantic import BaseModel

from nexus_shared.events.catalog import EventType
from nexus_shared.events.registry import SchemaRegistry
from event_fabric.config import Settings
from event_fabric.container import Container


class TickPayload(BaseModel):
    symbol: str
    ltp: float


class RegimePayload(BaseModel):
    regime: str


@pytest.fixture
def registry() -> SchemaRegistry:
    reg = SchemaRegistry(strict=True)
    reg.register(EventType.TICK_RECEIVED, 1, TickPayload)
    reg.register(EventType.MARKET_REGIME_CHANGED, 1, RegimePayload)
    return reg


@pytest.fixture
def settings() -> Settings:
    return Settings(
        EVENT_FABRIC_DATABASE_URL="sqlite+aiosqlite:///:memory:",
        auth_enabled=False,
        strict_schema_validation=True,
        event_signing_key="test-key",
    )


@pytest_asyncio.fixture
async def container(settings: Settings, registry: SchemaRegistry) -> Container:
    c = Container.build(settings, registry=registry)
    await c.startup()
    try:
        yield c
    finally:
        await c.shutdown()
