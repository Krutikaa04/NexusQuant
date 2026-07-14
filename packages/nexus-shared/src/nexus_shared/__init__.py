"""NexusQuant shared kernel.

Holds cross-context *contracts and primitives only* — the standard event envelope,
the canonical event-type catalog, and small domain primitives. Per SPEC-003, no
business logic lives here; bounded contexts depend on this package for the shapes
they exchange, never for behaviour they own.
"""

from nexus_shared.events.catalog import EventType
from nexus_shared.events.envelope import EventEnvelope, EventMetadata
from nexus_shared.primitives.identifiers import new_correlation_id, new_event_id
from nexus_shared.primitives.time import utc_now

__all__ = [
    "EventEnvelope",
    "EventMetadata",
    "EventType",
    "new_event_id",
    "new_correlation_id",
    "utc_now",
]
