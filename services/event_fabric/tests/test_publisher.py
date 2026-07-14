"""Publisher pipeline tests: validation, persistence, routing, dead-lettering (SPEC-005)."""

from __future__ import annotations

import asyncio

import pytest

from nexus_shared.events.catalog import EventCategory, EventType
from nexus_shared.events.envelope import EventEnvelope
from event_fabric.container import Container
from event_fabric.repositories.event_store import EventStoreRepository, ReplayQuery
from event_fabric.services.publisher import DeadLetterReason


def tick(symbol: str = "RELIANCE", ltp: float = 2950.0) -> EventEnvelope:
    return EventEnvelope(
        event_type=EventType.TICK_RECEIVED,
        producer="market_intelligence",
        aggregate_id=symbol,
        payload={"symbol": symbol, "ltp": ltp},
    )


async def test_valid_event_is_persisted_and_sequenced(container: Container) -> None:
    result = await container.publisher.publish(tick())
    assert result.accepted
    assert result.sequence == 1
    async with container.database.session() as session:
        assert await EventStoreRepository(session).count() == 1


async def test_signature_is_attached_and_deterministic(container: Container) -> None:
    env = tick()
    await container.publisher.publish(env)
    async with container.database.session() as session:
        stored = await EventStoreRepository(session).get_by_event_id(env.event_id)
    assert stored is not None
    assert stored.metadata.signature == container.publisher.sign(env)


async def test_invalid_payload_is_dead_lettered(container: Container) -> None:
    bad = EventEnvelope(
        event_type=EventType.TICK_RECEIVED,
        producer="market_intelligence",
        payload={"symbol": "RELIANCE"},  # missing ltp
    )
    result = await container.publisher.publish(bad)
    assert not result.accepted
    assert result.dead_letter_reason == DeadLetterReason.INVALID_SCHEMA
    async with container.database.session() as session:
        repo = EventStoreRepository(session)
        assert await repo.count() == 0
        assert await repo.count_dead_letters() == 1


async def test_unknown_version_is_dead_lettered(container: Container) -> None:
    env = EventEnvelope(
        event_type=EventType.TICK_RECEIVED,
        event_version=99,
        producer="market_intelligence",
        payload={"symbol": "TCS", "ltp": 1.0},
    )
    result = await container.publisher.publish(env)
    assert result.dead_letter_reason == DeadLetterReason.UNKNOWN_VERSION


async def test_subscribers_receive_matching_events(container: Container) -> None:
    seen: list[EventEnvelope] = []

    async def handler(env: EventEnvelope) -> None:
        seen.append(env)

    container.subscriptions.subscribe(
        "test-consumer", handler, categories=[EventCategory.MARKET]
    )
    await container.publisher.publish(tick("INFY", 1500.0))
    await asyncio.sleep(0)  # let the dispatch task settle
    assert len(seen) == 1
    assert seen[0].payload["symbol"] == "INFY"


async def test_failing_consumer_is_isolated(container: Container) -> None:
    good_seen: list[EventEnvelope] = []

    async def bad(_: EventEnvelope) -> None:
        raise RuntimeError("boom")

    async def good(env: EventEnvelope) -> None:
        good_seen.append(env)

    container.subscriptions.subscribe("bad", bad, event_types=[EventType.TICK_RECEIVED])
    container.subscriptions.subscribe("good", good, event_types=[EventType.TICK_RECEIVED])
    result = await container.publisher.publish(tick())
    assert result.accepted  # publish still succeeds despite a bad consumer
    assert len(good_seen) == 1
    stats = container.subscriptions.stats()
    assert stats["bad"]["failed"] == 1
    assert stats["good"]["delivered"] == 1


async def test_per_aggregate_ordering_preserved(container: Container) -> None:
    for ltp in (100.0, 101.0, 102.0):
        await container.publisher.publish(tick("SBIN", ltp))
    async with container.database.session() as session:
        rows = await EventStoreRepository(session).scan(
            ReplayQuery(aggregate_id="SBIN")
        )
    sequences = [seq for seq, _ in rows]
    prices = [env.payload["ltp"] for _, env in rows]
    assert sequences == sorted(sequences)  # monotonic ordering
    assert prices == [100.0, 101.0, 102.0]
