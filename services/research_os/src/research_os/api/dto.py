"""Request/response models for the Research OS API (SPEC-007 §6)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from research_os.db.models import (
    ExperimentRecord,
    HypothesisRecord,
    ProjectRecord,
    ReviewRecord,
    StatusHistoryRecord,
)
from research_os.domain.lifecycle import ProjectStatus, next_statuses
from research_os.domain.vocabulary import ExperimentStatus, ReviewDecision


class HealthResponse(BaseModel):
    status: str
    service: str
    environment: str
    migrations_applied: list[str]


# --- requests ---


class ProjectCreate(BaseModel):
    name: str = Field(min_length=3, max_length=200)
    owner: str = Field(min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=5000)
    tags: list[str] = Field(default_factory=list, max_length=12)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProjectUpdate(BaseModel):
    description: str | None = Field(default=None, max_length=5000)
    tags: list[str] | None = Field(default=None, max_length=12)
    metadata: dict[str, Any] | None = None


class TransitionRequest(BaseModel):
    to_status: ProjectStatus
    actor: str = Field(min_length=1, max_length=128)
    note: str | None = Field(default=None, max_length=1000)


class HypothesisCreate(BaseModel):
    project_id: str
    statement: str = Field(min_length=8, max_length=5000)
    success_criteria: str = Field(min_length=3, max_length=5000)
    notes: str | None = Field(default=None, max_length=5000)


class HypothesisUpdate(BaseModel):
    statement: str | None = Field(default=None, min_length=8, max_length=5000)
    success_criteria: str | None = Field(default=None, min_length=3, max_length=5000)
    notes: str | None = Field(default=None, max_length=5000)
    archived: bool | None = None


class ExperimentCreate(BaseModel):
    project_id: str
    name: str = Field(min_length=3, max_length=200)
    dataset_version: str = Field(min_length=1, max_length=128)
    feature_version: str = Field(min_length=1, max_length=128)
    hypothesis_id: str | None = None
    notes: str | None = Field(default=None, max_length=5000)


class ExperimentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=3, max_length=200)
    notes: str | None = Field(default=None, max_length=5000)


class ExperimentComplete(BaseModel):
    status: ExperimentStatus
    metrics: dict[str, Any] = Field(default_factory=dict)
    notes: str | None = Field(default=None, max_length=5000)


class ReviewCreate(BaseModel):
    project_id: str
    reviewer: str = Field(min_length=1, max_length=128)
    decision: ReviewDecision
    comments: str = Field(min_length=3, max_length=5000)


# --- responses ---


class HypothesisView(BaseModel):
    id: str
    project_id: str
    statement: str
    success_criteria: str
    notes: str | None
    archived: bool
    created_at: str
    updated_at: str

    @classmethod
    def of(cls, h: HypothesisRecord) -> "HypothesisView":
        return cls(
            id=h.id, project_id=h.project_id, statement=h.statement,
            success_criteria=h.success_criteria, notes=h.notes, archived=h.archived,
            created_at=h.created_at.isoformat(), updated_at=h.updated_at.isoformat(),
        )


class ExperimentView(BaseModel):
    id: str
    project_id: str
    hypothesis_id: str | None
    name: str
    dataset_version: str
    feature_version: str
    status: str
    metrics: dict[str, Any]
    notes: str | None
    created_at: str
    started_at: str | None
    completed_at: str | None

    @classmethod
    def of(cls, e: ExperimentRecord) -> "ExperimentView":
        return cls(
            id=e.id, project_id=e.project_id, hypothesis_id=e.hypothesis_id, name=e.name,
            dataset_version=e.dataset_version, feature_version=e.feature_version,
            status=e.status, metrics=e.metrics, notes=e.notes,
            created_at=e.created_at.isoformat(),
            started_at=e.started_at.isoformat() if e.started_at else None,
            completed_at=e.completed_at.isoformat() if e.completed_at else None,
        )


class ReviewView(BaseModel):
    id: str
    project_id: str
    reviewer: str
    decision: str
    comments: str
    stage: str
    created_at: str

    @classmethod
    def of(cls, r: ReviewRecord) -> "ReviewView":
        return cls(
            id=r.id, project_id=r.project_id, reviewer=r.reviewer, decision=r.decision,
            comments=r.comments, stage=r.stage, created_at=r.created_at.isoformat(),
        )


class TransitionView(BaseModel):
    from_status: str | None
    to_status: str
    actor: str
    note: str | None
    at: str

    @classmethod
    def of(cls, t: StatusHistoryRecord) -> "TransitionView":
        return cls(
            from_status=t.from_status, to_status=t.to_status, actor=t.actor,
            note=t.note, at=t.created_at.isoformat(),
        )


class ProjectSummary(BaseModel):
    id: str
    name: str
    owner: str
    description: str | None
    status: str
    tags: list[str]
    hypothesis_count: int
    experiment_count: int
    review_count: int
    allowed_transitions: list[str]
    created_at: str
    updated_at: str

    @classmethod
    def of(cls, p: ProjectRecord) -> "ProjectSummary":
        return cls(
            id=p.id, name=p.name, owner=p.owner, description=p.description,
            status=p.status, tags=p.tags,
            hypothesis_count=sum(1 for h in p.hypotheses if not h.archived),
            experiment_count=len(p.experiments),
            review_count=len(p.reviews),
            allowed_transitions=[s.value for s in next_statuses(ProjectStatus(p.status))],
            created_at=p.created_at.isoformat(), updated_at=p.updated_at.isoformat(),
        )


class ProjectDetail(ProjectSummary):
    metadata: dict[str, Any]
    hypotheses: list[HypothesisView]
    experiments: list[ExperimentView]
    reviews: list[ReviewView]

    @classmethod
    def of_full(cls, p: ProjectRecord, history: list[StatusHistoryRecord] | None = None) -> "ProjectDetail":
        base = ProjectSummary.of(p)
        return cls(
            **base.model_dump(),
            metadata=p.extra,
            hypotheses=[HypothesisView.of(h) for h in p.hypotheses],
            experiments=[ExperimentView.of(e) for e in reversed(p.experiments)],
            reviews=[ReviewView.of(r) for r in reversed(p.reviews)],
        )
