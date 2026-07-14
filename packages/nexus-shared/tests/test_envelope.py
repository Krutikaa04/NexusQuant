"""Unit tests for the standard event envelope (SPEC-005 §4, §12)."""

from __future__ import annotations

from uuid import UUID

import pytest
from pydantic import ValidationError

from nexus_shared.events.catalog import EventCategory, EventType
from nexus_shared.events.envelope import EventEnvelope


def make_envelope(**overrides) -> EventEnvelope:
    base = dict(
        event_type=EventType.TICK_RECEIVED,
        producer="market_intelligence",
        payload={"symbol": "RELIANCE", "ltp": 2950.5},
    )
    base.update(overrides)
    return EventEnvelope(**base)


def test_envelope_populates_defaults() -> None:
    env = make_envelope()
    assert isinstance(env.event_id, UUID)
    assert isinstance(env.correlation_id, UUID)
    assert env.event_version == 1
    assert env.metadata.schema_version == 1
    assert env.timestamp_utc.tzinfo is not None  # timezone-aware UTC


def test_envelope_is_immutable() -> None:
    env = make_envelope()
    with pytest.raises(ValidationError):
        env.event_version = 2  # type: ignore[misc]


def test_category_derived_from_type() -> None:
    assert make_envelope().category is EventCategory.MARKET
    assert EventType.ORDER_FILLED.category is EventCategory.EXECUTION


def test_producer_is_required_and_nonempty() -> None:
    with pytest.raises(ValidationError):
        EventEnvelope(event_type=EventType.TICK_RECEIVED, producer="")


def test_event_version_must_be_positive() -> None:
    with pytest.raises(ValidationError):
        make_envelope(event_version=0)


def test_with_correlation_chains_causation_without_mutation() -> None:
    parent = make_envelope()
    child = make_envelope().with_correlation(parent.correlation_id)
    # original untouched (immutability); child records causal linkage
    assert child.correlation_id == parent.correlation_id
    assert child.metadata.causation_id is not None
    assert child.event_id != parent.event_id
