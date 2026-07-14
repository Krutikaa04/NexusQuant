"""The standard event envelope (SPEC-005 §4).

Every message that crosses a bounded context is wrapped in an :class:`EventEnvelope`.
Envelopes are **immutable** (SPEC-005 §4): once constructed their fields cannot change,
which guarantees that a persisted event and a replayed event are byte-for-byte identical.

The envelope carries an opaque ``payload`` dict. The *shape* of each payload is owned by
the producing context and registered in :mod:`nexus_shared.events.registry`; the envelope
itself is deliberately payload-agnostic so the fabric never needs domain knowledge.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from nexus_shared.events.catalog import EventCategory, EventType
from nexus_shared.primitives.identifiers import new_correlation_id, new_event_id
from nexus_shared.primitives.time import utc_now


class EventMetadata(BaseModel):
    """Transport-level, non-domain annotations attached to an event.

    Metadata may be extended freely without a schema-version bump because it never
    carries business meaning — it exists for tracing, security and operability.
    """

    model_config = ConfigDict(frozen=True, extra="allow")

    schema_version: int = Field(default=1, ge=1, description="Envelope schema version.")
    causation_id: UUID | None = Field(
        default=None, description="Event id that directly caused this event, if any."
    )
    signature: str | None = Field(
        default=None, description="HMAC signature of the canonical payload (SPEC-005 §11)."
    )
    trace_id: str | None = Field(default=None, description="Distributed-trace identifier.")


class EventEnvelope(BaseModel):
    """Immutable, versioned envelope wrapping a single domain event (SPEC-005 §4)."""

    model_config = ConfigDict(frozen=True)

    event_id: UUID = Field(default_factory=new_event_id)
    event_type: EventType
    event_version: int = Field(default=1, ge=1, description="Payload schema version (SemVer major).")
    timestamp_utc: datetime = Field(default_factory=utc_now)
    producer: str = Field(min_length=1, description="Owning bounded context, e.g. 'market_intelligence'.")
    correlation_id: UUID = Field(default_factory=new_correlation_id)
    aggregate_id: str | None = Field(
        default=None,
        description="Aggregate this event belongs to; per-aggregate ordering key (SPEC-005 §5).",
    )
    payload: dict[str, Any] = Field(default_factory=dict)
    metadata: EventMetadata = Field(default_factory=EventMetadata)

    @property
    def category(self) -> EventCategory:
        """Routing category derived from the event type."""
        return self.event_type.category

    def with_correlation(self, correlation_id: UUID) -> EventEnvelope:
        """Return a copy that participates in an existing correlated flow.

        Because envelopes are frozen, causal chaining is expressed by producing a new
        envelope rather than mutating this one. The new envelope records this envelope's
        id as its ``causation_id``.
        """
        return self.model_copy(
            update={
                "correlation_id": correlation_id,
                "metadata": self.metadata.model_copy(update={"causation_id": self.event_id}),
            }
        )
