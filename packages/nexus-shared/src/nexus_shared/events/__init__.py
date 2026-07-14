"""Event contracts: the canonical catalog, the standard envelope, and the schema registry."""

from nexus_shared.events.catalog import EventCategory, EventType
from nexus_shared.events.envelope import EventEnvelope, EventMetadata
from nexus_shared.events.registry import (
    SchemaRegistry,
    UnknownEventTypeError,
    UnknownEventVersionError,
)

__all__ = [
    "EventCategory",
    "EventType",
    "EventEnvelope",
    "EventMetadata",
    "SchemaRegistry",
    "UnknownEventTypeError",
    "UnknownEventVersionError",
]
