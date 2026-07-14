"""Request/response models for the fabric's REST API (SPEC-005 §7)."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from nexus_shared.events.catalog import EventType


class PublishRequest(BaseModel):
    """Ingress payload for publishing a single event (the fabric wraps it in an envelope)."""

    event_type: EventType
    event_version: int = Field(default=1, ge=1)
    producer: str = Field(min_length=1)
    correlation_id: UUID | None = None
    aggregate_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class PublishResponse(BaseModel):
    accepted: bool
    event_id: UUID | None = None
    sequence: int | None = None
    dead_letter_reason: str | None = None


class ReplayRequest(BaseModel):
    event_type: EventType | None = None
    correlation_id: UUID | None = None
    aggregate_id: str | None = None
    from_sequence: int = Field(default=0, ge=0)
    since: datetime | None = None
    until: datetime | None = None
    limit: int | None = Field(default=None, ge=1)
    dispatch: bool = Field(
        default=False, description="Re-deliver matched events to live consumers."
    )


class ReplayResponse(BaseModel):
    replayed: int
    last_sequence: int
    dispatched: bool


class HealthResponse(BaseModel):
    status: str
    service: str
    environment: str


class MetricsResponse(BaseModel):
    events_stored: int
    dead_letters: int
    published: int
    dead_lettered: int
    active_consumers: int
    ws_connections: int
    consumers: dict[str, dict[str, int]]


class SchemaResponse(BaseModel):
    event_type: EventType
    registered_versions: list[int]
    latest_version: int | None
