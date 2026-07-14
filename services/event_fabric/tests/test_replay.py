"""Replay determinism tests (SPEC-005 §10)."""

from __future__ import annotations

from nexus_shared.events.catalog import EventType
from nexus_shared.events.envelope import EventEnvelope
from event_fabric.container import Container
from event_fabric.repositories.event_store import ReplayQuery


def tick(symbol: str, ltp: float) -> EventEnvelope:
    return EventEnvelope(
        event_type=EventType.TICK_RECEIVED,
        producer="market_intelligence",
        aggregate_id=symbol,
        payload={"symbol": symbol, "ltp": ltp},
    )


async def seed(container: Container) -> None:
    await container.publisher.publish(tick("A", 1.0))
    await container.publisher.publish(tick("B", 2.0))
    await container.publisher.publish(tick("A", 3.0))


async def test_replay_is_deterministic(container: Container) -> None:
    await seed(container)
    first = await container.replay.collect(ReplayQuery())
    second = await container.replay.collect(ReplayQuery())
    assert [e.event_id for e in first] == [e.event_id for e in second]
    assert [e.payload["ltp"] for e in first] == [1.0, 2.0, 3.0]


async def test_replay_filters_by_aggregate(container: Container) -> None:
    await seed(container)
    events = await container.replay.collect(ReplayQuery(aggregate_id="A"))
    assert [e.payload["ltp"] for e in events] == [1.0, 3.0]


async def test_replay_dispatches_to_consumers(container: Container) -> None:
    seen: list[EventEnvelope] = []

    async def handler(env: EventEnvelope) -> None:
        seen.append(env)

    await seed(container)
    container.subscriptions.subscribe(
        "replay-consumer", handler, event_types=[EventType.TICK_RECEIVED]
    )
    report = await container.replay.replay(ReplayQuery(), dispatch=True)
    assert report.replayed == 3
    assert len(seen) == 3


async def test_replay_from_sequence_cursor(container: Container) -> None:
    await seed(container)
    events = await container.replay.collect(ReplayQuery(from_sequence=1))
    # excludes sequence 1, returns the remaining two
    assert [e.payload["ltp"] for e in events] == [2.0, 3.0]
