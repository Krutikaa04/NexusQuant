"""Payload contracts for the events this context publishes (SPEC-007 §7).

Exactly the six events the spec defines — no additions. Registered with the shared schema
registry so the Event Fabric validates them at publish time.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from nexus_shared.events.catalog import EventType
from nexus_shared.events.registry import default_registry


class ResearchProjectCreatedPayload(BaseModel):
    project_id: str
    name: str
    owner: str
    tags: list[str] = Field(default_factory=list)


class HypothesisCreatedPayload(BaseModel):
    hypothesis_id: str
    project_id: str
    statement: str
    success_criteria: str


class ExperimentStartedPayload(BaseModel):
    experiment_id: str
    project_id: str
    name: str
    dataset_version: str
    feature_version: str


class ExperimentCompletedPayload(BaseModel):
    experiment_id: str
    project_id: str
    status: str  # completed | failed | cancelled
    metrics: dict = Field(default_factory=dict)


class ResearchReviewedPayload(BaseModel):
    review_id: str
    project_id: str
    reviewer: str
    decision: str
    stage: str


class StrategyPromotedPayload(BaseModel):
    project_id: str
    name: str
    from_status: str
    to_status: str
    actor: str


def register_published_schemas() -> None:
    default_registry.register(
        EventType.RESEARCH_PROJECT_CREATED, 1, ResearchProjectCreatedPayload
    )
    default_registry.register(EventType.HYPOTHESIS_CREATED, 1, HypothesisCreatedPayload)
    default_registry.register(EventType.EXPERIMENT_STARTED, 1, ExperimentStartedPayload)
    default_registry.register(EventType.EXPERIMENT_COMPLETED, 1, ExperimentCompletedPayload)
    default_registry.register(EventType.RESEARCH_REVIEWED, 1, ResearchReviewedPayload)
    default_registry.register(EventType.STRATEGY_PROMOTED, 1, StrategyPromotedPayload)
