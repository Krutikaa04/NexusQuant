"""Deterministic replay engine (SPEC-005 §4 replay, §10 determinism).

Replay reads previously-persisted events from the immutable store, in total-sequence
order, and re-delivers them to consumers (or returns them to an API caller). Because the
store is append-only and ordering is by the monotonic ``sequence``, a replay over the same
query always reproduces the identical event stream — the property downstream backtests and
audits rely on (SPEC-002 ADR-004, SPEC-005 §10).

Replay never re-persists events and never mutates offsets unless explicitly asked to, so it
is side-effect-free with respect to the event store.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from nexus_shared.events.envelope import EventEnvelope
from event_fabric.db.session import Database
from event_fabric.repositories.event_store import EventStoreRepository, ReplayQuery
from event_fabric.services.subscriber import SubscriptionRegistry

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ReplayReport:
    replayed: int
    last_sequence: int
    dispatched: bool


class ReplayService:
    def __init__(
        self,
        database: Database,
        subscriptions: SubscriptionRegistry,
        *,
        batch_size: int = 500,
    ) -> None:
        self._db = database
        self._subscriptions = subscriptions
        self._batch_size = batch_size

    async def collect(self, query: ReplayQuery) -> list[EventEnvelope]:
        """Return the matching events in deterministic order without side effects."""
        async with self._db.session() as session:
            repo = EventStoreRepository(session)
            rows = await repo.scan(query)
        return [env for _, env in rows]

    async def replay(self, query: ReplayQuery, *, dispatch: bool = False) -> ReplayReport:
        """Stream matching events in batches; optionally re-dispatch to consumers.

        Batches are bounded by ``batch_size`` (SPEC-005 §9 ``REPLAY_BATCH_SIZE``) so a
        large replay does not materialise the whole store in memory.
        """
        cursor = query.from_sequence
        total = 0
        last_sequence = cursor
        while True:
            async with self._db.session() as session:
                repo = EventStoreRepository(session)
                batch = await repo.scan(
                    ReplayQuery(
                        event_type=query.event_type,
                        correlation_id=query.correlation_id,
                        aggregate_id=query.aggregate_id,
                        from_sequence=cursor,
                        since=query.since,
                        until=query.until,
                        limit=self._batch_size,
                    )
                )
            if not batch:
                break
            for sequence, envelope in batch:
                if dispatch:
                    await self._subscriptions.dispatch(envelope)
                last_sequence = sequence
                total += 1
            cursor = batch[-1][0]
            if query.limit is not None and total >= query.limit:
                break

        logger.info("replayed %d events (dispatch=%s)", total, dispatch)
        return ReplayReport(replayed=total, last_sequence=last_sequence, dispatched=dispatch)
