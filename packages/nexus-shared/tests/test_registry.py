"""Unit tests for the schema registry (SPEC-005 §5 dead-letter classification)."""

from __future__ import annotations

import pytest
from pydantic import BaseModel, ValidationError

from nexus_shared.events.catalog import EventType
from nexus_shared.events.envelope import EventEnvelope
from nexus_shared.events.registry import (
    SchemaRegistry,
    UnknownEventTypeError,
    UnknownEventVersionError,
)


class TickPayload(BaseModel):
    symbol: str
    ltp: float


def envelope(payload: dict, version: int = 1) -> EventEnvelope:
    return EventEnvelope(
        event_type=EventType.TICK_RECEIVED,
        event_version=version,
        producer="market_intelligence",
        payload=payload,
    )


def test_valid_payload_parses() -> None:
    reg = SchemaRegistry()
    reg.register(EventType.TICK_RECEIVED, 1, TickPayload)
    parsed = reg.validate(envelope({"symbol": "TCS", "ltp": 3900.0}))
    assert isinstance(parsed, TickPayload)
    assert parsed.symbol == "TCS"


def test_unknown_type_rejected_in_strict_mode() -> None:
    reg = SchemaRegistry(strict=True)
    with pytest.raises(UnknownEventTypeError):
        reg.validate(envelope({"symbol": "TCS", "ltp": 1.0}))


def test_unknown_type_passes_in_lenient_mode() -> None:
    reg = SchemaRegistry(strict=False)
    assert reg.validate(envelope({"anything": True})) is None


def test_unknown_version_rejected() -> None:
    reg = SchemaRegistry()
    reg.register(EventType.TICK_RECEIVED, 1, TickPayload)
    with pytest.raises(UnknownEventVersionError):
        reg.validate(envelope({"symbol": "TCS", "ltp": 1.0}, version=2))


def test_invalid_payload_raises_validation_error() -> None:
    reg = SchemaRegistry()
    reg.register(EventType.TICK_RECEIVED, 1, TickPayload)
    with pytest.raises(ValidationError):
        reg.validate(envelope({"symbol": "TCS"}))  # missing ltp
