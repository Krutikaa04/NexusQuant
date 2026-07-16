"""Supporting enums for experiments and reviews (SPEC-007 §5)."""

from __future__ import annotations

from enum import Enum


class ExperimentStatus(str, Enum):
    """Run status of an experiment. The Research OS manages metadata and lifecycle only —
    actual execution belongs to the Validation Platform (out of scope, SPEC-007)."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


TERMINAL_EXPERIMENT_STATUSES = frozenset(
    {ExperimentStatus.COMPLETED, ExperimentStatus.FAILED, ExperimentStatus.CANCELLED}
)


class ReviewDecision(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    NEEDS_CHANGES = "needs_changes"
