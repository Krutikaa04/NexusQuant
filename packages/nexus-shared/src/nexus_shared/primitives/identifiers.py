"""Identifier factories. All aggregate and event identifiers are UUIDv4 (SPEC-006 §8)."""

from __future__ import annotations

from uuid import UUID, uuid4


def new_event_id() -> UUID:
    """A fresh, globally-unique event identifier."""
    return uuid4()


def new_correlation_id() -> UUID:
    """A fresh correlation identifier used to trace a causally-related flow of events."""
    return uuid4()


def ensure_uuid(value: str | UUID) -> UUID:
    """Coerce a string or UUID into a UUID, raising ``ValueError`` on malformed input."""
    return value if isinstance(value, UUID) else UUID(str(value))
