"""The Publisher — the single ingress for events into the fabric (SPEC-005 §14 step 2).

Publishing an event is a governed pipeline:

1. **Validate** the payload against the registered schema (SPEC-005 §5).
2. **Sign** the envelope (HMAC) so downstream consumers can verify integrity (§11).
3. **Persist** it immutably to the event store, assigning a global sequence (§8).
4. **Route** it to in-process subscribers and stream it to WebSocket channels (§2, §6).

Any envelope failing validation is diverted to the dead-letter queue with a typed reason
rather than raising to the caller — the caller's publish still "succeeds" operationally,
but the event does not enter the stream. Schema/version failures are terminal; the DLQ is
the audit trail (§5).
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
from dataclasses import dataclass

from pydantic import ValidationError

from nexus_shared.events.envelope import EventEnvelope
from nexus_shared.events.registry import (
    SchemaRegistry,
    UnknownEventTypeError,
    UnknownEventVersionError,
)
from event_fabric.db.session import Database
from event_fabric.repositories.event_store import EventStoreRepository
from event_fabric.services.subscriber import SubscriptionRegistry

logger = logging.getLogger(__name__)


class DeadLetterReason:
    UNKNOWN_TYPE = "unknown_type"
    UNKNOWN_VERSION = "unknown_version"
    INVALID_SCHEMA = "invalid_schema"
    PROCESSING_FAILURE = "processing_failure"


@dataclass(frozen=True, slots=True)
class PublishResult:
    accepted: bool
    sequence: int | None = None
    dead_letter_reason: str | None = None


# A streaming sink is anything that can accept an envelope for fan-out (the WS gateway).
class StreamSink:
    async def broadcast(self, envelope: EventEnvelope) -> None:  # pragma: no cover - interface
        raise NotImplementedError


class Publisher:
    def __init__(
        self,
        database: Database,
        registry: SchemaRegistry,
        subscriptions: SubscriptionRegistry,
        *,
        signing_key: str,
        stream_sink: StreamSink | None = None,
    ) -> None:
        self._db = database
        self._registry = registry
        self._subscriptions = subscriptions
        self._signing_key = signing_key.encode("utf-8")
        self._stream_sink = stream_sink
        self._published = 0
        self._dead_lettered = 0

    def sign(self, envelope: EventEnvelope) -> str:
        """Deterministic HMAC-SHA256 over the canonical (type, version, payload)."""
        canonical = json.dumps(
            {
                "event_type": envelope.event_type.value,
                "event_version": envelope.event_version,
                "payload": envelope.payload,
            },
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
        return hmac.new(self._signing_key, canonical, hashlib.sha256).hexdigest()

    async def publish(self, envelope: EventEnvelope) -> PublishResult:
        # 1. validate
        try:
            self._registry.validate(envelope)
        except UnknownEventTypeError as exc:
            return await self._to_dead_letter(envelope, DeadLetterReason.UNKNOWN_TYPE, str(exc))
        except UnknownEventVersionError as exc:
            return await self._to_dead_letter(envelope, DeadLetterReason.UNKNOWN_VERSION, str(exc))
        except ValidationError as exc:
            return await self._to_dead_letter(envelope, DeadLetterReason.INVALID_SCHEMA, str(exc))

        # 2. sign (attach signature to metadata without mutating the frozen original)
        signed = envelope.model_copy(
            update={"metadata": envelope.metadata.model_copy(update={"signature": self.sign(envelope)})}
        )

        # 3. persist immutably
        async with self._db.session() as session:
            repo = EventStoreRepository(session)
            sequence = await repo.append(signed)
            await repo.record_schema_version(signed.event_type, signed.event_version)
            await session.commit()

        self._published += 1

        # 4. route to in-process consumers and stream to WebSocket channels.
        # Delivery failures here are per-consumer and already isolated; the event is
        # already durably stored, so a consumer can always catch up via replay.
        await self._subscriptions.dispatch(signed)
        if self._stream_sink is not None:
            try:
                await self._stream_sink.broadcast(signed)
            except Exception:  # pragma: no cover - streaming is best-effort
                logger.exception("stream broadcast failed for %s", signed.event_id)

        return PublishResult(accepted=True, sequence=sequence)

    async def _to_dead_letter(
        self, envelope: EventEnvelope, reason: str, detail: str
    ) -> PublishResult:
        async with self._db.session() as session:
            repo = EventStoreRepository(session)
            await repo.dead_letter(
                reason=reason,
                error_detail=detail,
                envelope=envelope.model_dump(mode="json"),
                event_id=str(envelope.event_id),
                event_type=envelope.event_type.value,
                event_version=envelope.event_version,
            )
            await session.commit()
        self._dead_lettered += 1
        logger.warning("dead-lettered %s: %s", envelope.event_type.value, reason)
        return PublishResult(accepted=False, dead_letter_reason=reason)

    @property
    def metrics(self) -> dict[str, int]:
        return {"published": self._published, "dead_lettered": self._dead_lettered}
