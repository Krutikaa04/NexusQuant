"""Event schema registry (supports SPEC-005 §5 dead-letter classification).

The Event Fabric owns *routing and validation* but not the *shape* of any payload —
those are owned by producing contexts (SPEC-003). This registry is the shared mechanism
by which a context declares "event ``X`` at version ``v`` has this payload shape". The
fabric consults the registry to decide whether an incoming envelope is:

* well-formed        → route and persist,
* an unknown type    → dead-letter (``UnknownEventTypeError``),
* an unknown version → dead-letter (``UnknownEventVersionError``),
* schema-invalid     → dead-letter (pydantic ``ValidationError``).

Registration is done by the owning context at import time, keeping business payload
shapes out of the shared kernel while still giving the fabric a validation contract.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel

from nexus_shared.events.catalog import EventType

if TYPE_CHECKING:
    from nexus_shared.events.envelope import EventEnvelope


class UnknownEventTypeError(KeyError):
    """Raised when an envelope references an event type with no registered schema."""


class UnknownEventVersionError(KeyError):
    """Raised when an event type is known but the specific version is not registered."""


class SchemaRegistry:
    """A registry mapping ``(EventType, version) → payload model``.

    ``strict`` controls the treatment of *entirely unregistered* event types. When
    strict (the default), an unregistered type is rejected so that undocumented events
    cannot silently traverse the fabric. When lenient, unregistered types pass through
    unvalidated — useful in early development before every context has declared schemas.
    """

    def __init__(self, *, strict: bool = True) -> None:
        self._schemas: dict[EventType, dict[int, type[BaseModel]]] = {}
        self._strict = strict

    def register(
        self, event_type: EventType, version: int, payload_model: type[BaseModel]
    ) -> None:
        """Declare the payload model for a given event type and version."""
        if version < 1:
            raise ValueError("event version must be >= 1")
        self._schemas.setdefault(event_type, {})[version] = payload_model

    def is_registered(self, event_type: EventType) -> bool:
        return event_type in self._schemas

    def model_for(self, event_type: EventType, version: int) -> type[BaseModel] | None:
        return self._schemas.get(event_type, {}).get(version)

    def validate(self, envelope: EventEnvelope) -> BaseModel | None:
        """Validate an envelope's payload against its registered schema.

        Returns the parsed payload model (or ``None`` when the type is unregistered and
        the registry is lenient). Raises :class:`UnknownEventTypeError`,
        :class:`UnknownEventVersionError`, or pydantic ``ValidationError`` on failure —
        each of which the fabric maps to a dead-letter reason.
        """
        versions = self._schemas.get(envelope.event_type)
        if versions is None:
            if self._strict:
                raise UnknownEventTypeError(envelope.event_type.value)
            return None

        model = versions.get(envelope.event_version)
        if model is None:
            raise UnknownEventVersionError(
                f"{envelope.event_type.value} v{envelope.event_version}"
            )

        return model.model_validate(envelope.payload)


# The process-wide default registry. Contexts register their payload schemas against
# this instance at import time; the Event Fabric validates against it.
default_registry = SchemaRegistry()
