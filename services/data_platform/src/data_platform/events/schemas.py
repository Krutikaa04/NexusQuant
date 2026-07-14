"""Payload contracts for the events the Data Platform consumes (SPEC-006 §7).

These declare the shape the Data Platform *expects* from producing contexts. They are
registered with the shared schema registry so the Event Fabric validates them before
delivery, and so this service fails fast on a malformed upstream event.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from nexus_shared.events.catalog import EventType
from nexus_shared.events.registry import default_registry


class DatasetCreatedPayload(BaseModel):
    dataset_id: str
    name: str
    namespace: str = "default"
    description: str | None = None
    content_hash: str = Field(min_length=8)
    storage_uri: str | None = None
    row_count: int | None = None
    columns: list[str] = Field(default_factory=list)


class FeatureVersionCreatedPayload(BaseModel):
    feature_id: str
    name: str
    namespace: str = "default"
    version: int = Field(ge=1)
    content_hash: str = Field(min_length=8)
    definition: dict = Field(default_factory=dict)
    # Lineage: the dataset version this feature was engineered from.
    upstream_dataset_version_id: str | None = None


class ModelValidatedPayload(BaseModel):
    model_id: str
    name: str
    namespace: str = "default"
    version: int = Field(ge=1)
    content_hash: str = Field(min_length=8)
    metrics: dict = Field(default_factory=dict)
    storage_uri: str | None = None
    # Lineage: the feature versions this model consumes.
    upstream_feature_version_ids: list[str] = Field(default_factory=list)


def register_consumed_schemas() -> None:
    """Register consumed-event payload schemas with the process-wide registry."""
    default_registry.register(EventType.DATASET_CREATED, 1, DatasetCreatedPayload)
    default_registry.register(EventType.FEATURE_VERSION_CREATED, 1, FeatureVersionCreatedPayload)
    default_registry.register(EventType.MODEL_VALIDATED, 1, ModelValidatedPayload)
