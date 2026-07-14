"""Test fixtures: isolated in-memory DB, in-memory cache, and a capturing publisher."""

from __future__ import annotations

import pytest
import pytest_asyncio

from nexus_shared.events.catalog import EventType
from nexus_shared.events.envelope import EventEnvelope
from data_platform.config import Settings
from data_platform.container import Container
from data_platform.events.publisher import InMemoryEventPublisher


@pytest.fixture
def settings() -> Settings:
    return Settings(
        DATA_PLATFORM_DATABASE_URL="sqlite+aiosqlite:///:memory:",
        auth_enabled=False,
        cache_ttl=300,
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


def build_dataset_event(
    *, name: str = "nifty_daily", namespace: str = "market", content_hash: str = "hash_ds_0001"
) -> EventEnvelope:
    return EventEnvelope(
        event_type=EventType.DATASET_CREATED,
        producer="research_os",
        payload={
            "dataset_id": "ds-123",
            "name": name,
            "namespace": namespace,
            "description": "NIFTY daily OHLCV",
            "content_hash": content_hash,
            "storage_uri": "s3://datasets/nifty_daily/v1.parquet",
            "row_count": 5000,
            "columns": ["date", "open", "high", "low", "close", "volume"],
        },
    )


@pytest.fixture
def dataset_event():
    """Factory fixture producing a valid ``DatasetCreated`` envelope."""
    return build_dataset_event
