"""Repository over the immutable event store (SPEC-005 §8).

Encapsulates all persistence for events, consumer offsets, schema-version records, and
dead letters. Callers deal in :class:`EventEnvelope` and query filters; the mapping to
and from ORM rows never leaks past this boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from nexus_shared.events.catalog import EventType
from nexus_shared.events.envelope import EventEnvelope, EventMetadata
from nexus_shared.primitives.time import utc_now
from event_fabric.db.models import (
    ConsumerOffset,
    DeadLetterEvent,
    EventRecord,
    EventSchemaVersion,
)


@dataclass(frozen=True, slots=True)
class ReplayQuery:
    """Filters for a deterministic replay/scan (SPEC-005 §7 replay)."""

    event_type: EventType | None = None
    correlation_id: UUID | None = None
    aggregate_id: str | None = None
    from_sequence: int = 0
    since: datetime | None = None
    until: datetime | None = None
    limit: int | None = None


def _record_to_envelope(record: EventRecord) -> EventEnvelope:
    return EventEnvelope(
        event_id=UUID(record.event_id),
        event_type=EventType(record.event_type),
        event_version=record.event_version,
        timestamp_utc=record.timestamp_utc,
        producer=record.producer,
        correlation_id=UUID(record.correlation_id),
        aggregate_id=record.aggregate_id,
        payload=record.payload,
        metadata=EventMetadata.model_validate(record.event_metadata),
    )


class EventStoreRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def append(self, envelope: EventEnvelope) -> int:
        """Persist an envelope and return its assigned global sequence.

        The store is append-only; the caller is responsible for having validated the
        envelope before calling. Returns the monotonic ``sequence`` used for ordering
        and replay cursors.
        """
        record = EventRecord(
            event_id=str(envelope.event_id),
            event_type=envelope.event_type.value,
            event_version=envelope.event_version,
            timestamp_utc=envelope.timestamp_utc,
            producer=envelope.producer,
            correlation_id=str(envelope.correlation_id),
            aggregate_id=envelope.aggregate_id,
            payload=envelope.payload,
            event_metadata=envelope.metadata.model_dump(mode="json"),
        )
        self._session.add(record)
        await self._session.flush()  # populate autoincrement sequence
        return record.sequence

    async def get_by_event_id(self, event_id: UUID) -> EventEnvelope | None:
        stmt = select(EventRecord).where(EventRecord.event_id == str(event_id))
        record = (await self._session.execute(stmt)).scalar_one_or_none()
        return _record_to_envelope(record) if record else None

    async def scan(self, query: ReplayQuery) -> list[tuple[int, EventEnvelope]]:
        """Return ``(sequence, envelope)`` pairs matching ``query`` in total order.

        Ordering by ``sequence`` ascending makes replay deterministic (SPEC-005 §10):
        the same query always yields the same events in the same order.
        """
        stmt = select(EventRecord).where(EventRecord.sequence > query.from_sequence)
        if query.event_type is not None:
            stmt = stmt.where(EventRecord.event_type == query.event_type.value)
        if query.correlation_id is not None:
            stmt = stmt.where(EventRecord.correlation_id == str(query.correlation_id))
        if query.aggregate_id is not None:
            stmt = stmt.where(EventRecord.aggregate_id == query.aggregate_id)
        if query.since is not None:
            stmt = stmt.where(EventRecord.timestamp_utc >= query.since)
        if query.until is not None:
            stmt = stmt.where(EventRecord.timestamp_utc <= query.until)
        stmt = stmt.order_by(EventRecord.sequence.asc())
        if query.limit is not None:
            stmt = stmt.limit(query.limit)
        rows = (await self._session.execute(stmt)).scalars().all()
        return [(r.sequence, _record_to_envelope(r)) for r in rows]

    async def count(self) -> int:
        from sqlalchemy import func

        stmt = select(func.count()).select_from(EventRecord)
        return int((await self._session.execute(stmt)).scalar_one())

    # --- consumer offsets ---

    async def get_offset(self, consumer_name: str) -> int:
        stmt = select(ConsumerOffset).where(ConsumerOffset.consumer_name == consumer_name)
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return row.last_sequence if row else 0

    async def set_offset(self, consumer_name: str, sequence: int) -> None:
        stmt = select(ConsumerOffset).where(ConsumerOffset.consumer_name == consumer_name)
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        if row is None:
            self._session.add(
                ConsumerOffset(
                    consumer_name=consumer_name, last_sequence=sequence, updated_at=utc_now()
                )
            )
        else:
            row.last_sequence = sequence
            row.updated_at = utc_now()

    # --- schema version registry mirror ---

    async def record_schema_version(self, event_type: EventType, version: int) -> None:
        exists = await self._session.get(EventSchemaVersion, (event_type.value, version))
        if exists is None:
            self._session.add(
                EventSchemaVersion(
                    event_type=event_type.value, version=version, registered_at=utc_now()
                )
            )

    # --- dead letters ---

    async def dead_letter(
        self,
        *,
        reason: str,
        error_detail: str,
        envelope: dict,
        event_id: str | None = None,
        event_type: str | None = None,
        event_version: int | None = None,
    ) -> None:
        self._session.add(
            DeadLetterEvent(
                event_id=event_id,
                event_type=event_type,
                event_version=event_version,
                reason=reason,
                error_detail=error_detail[:4000],
                envelope=envelope,
                received_at=utc_now(),
            )
        )

    async def count_dead_letters(self) -> int:
        from sqlalchemy import func

        stmt = select(func.count()).select_from(DeadLetterEvent)
        return int((await self._session.execute(stmt)).scalar_one())
