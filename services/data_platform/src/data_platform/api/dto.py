"""Request/response models for the Data Platform API (SPEC-006 §6)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from nexus_shared.events.catalog import EventType


class HealthResponse(BaseModel):
    status: str
    service: str
    environment: str
    migrations_applied: list[str]


class IngestRequest(BaseModel):
    """Inbound event delivery from the Event Fabric subscriber (SPEC-006 §7 consumer)."""

    event_type: EventType
    event_version: int = Field(default=1, ge=1)
    producer: str = Field(min_length=1)
    correlation_id: UUID | None = None
    aggregate_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class IngestResponse(BaseModel):
    handled: bool
    idempotent: bool
    artifact_id: str | None = None
    version_id: str | None = None
    version: int | None = None
