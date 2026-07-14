"""Time primitives. Every timestamp in NexusQuant is timezone-aware UTC (SPEC-006 §8)."""

from __future__ import annotations

from datetime import datetime, timezone


def utc_now() -> datetime:
    """The current instant as a timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


def to_utc(moment: datetime) -> datetime:
    """Normalise any datetime to UTC. Naive datetimes are assumed to already be UTC."""
    if moment.tzinfo is None:
        return moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc)
