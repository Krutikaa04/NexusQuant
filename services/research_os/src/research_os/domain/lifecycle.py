"""The research lifecycle state machine (SPEC-007 §4).

The lifecycle is a strict linear progression:

    Draft → Active → Experimenting → Validated → Paper Trading
          → Production Candidate → Approved → Retired

Only single forward steps are legal; anything else raises
:class:`IllegalTransitionError`. Two transitions carry additional guards enforced by the
service layer (SPEC-007 §8):

* Draft → Active requires the project to have at least one active hypothesis.
* Production Candidate → Approved requires a successful review at that stage
  (when ``REVIEW_REQUIRED`` is enabled).

Once a project is Approved its research artifacts are immutable; Retired is terminal.
"""

from __future__ import annotations

from enum import Enum


class ProjectStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    EXPERIMENTING = "experimenting"
    VALIDATED = "validated"
    PAPER_TRADING = "paper_trading"
    PRODUCTION_CANDIDATE = "production_candidate"
    APPROVED = "approved"
    RETIRED = "retired"


_ORDER: list[ProjectStatus] = [
    ProjectStatus.DRAFT,
    ProjectStatus.ACTIVE,
    ProjectStatus.EXPERIMENTING,
    ProjectStatus.VALIDATED,
    ProjectStatus.PAPER_TRADING,
    ProjectStatus.PRODUCTION_CANDIDATE,
    ProjectStatus.APPROVED,
    ProjectStatus.RETIRED,
]

# Statuses whose research artifacts are frozen (SPEC-007 §8: immutable after approval).
IMMUTABLE_STATUSES: frozenset[ProjectStatus] = frozenset(
    {ProjectStatus.APPROVED, ProjectStatus.RETIRED}
)

# Statuses during which experiments may be created/updated.
EXPERIMENTATION_STATUSES: frozenset[ProjectStatus] = frozenset(
    {ProjectStatus.ACTIVE, ProjectStatus.EXPERIMENTING}
)


class IllegalTransitionError(ValueError):
    """Raised when a requested status change is not a legal lifecycle step."""

    def __init__(self, current: ProjectStatus, requested: ProjectStatus) -> None:
        self.current = current
        self.requested = requested
        super().__init__(
            f"illegal lifecycle transition: {current.value} → {requested.value}; "
            f"allowed next: {[s.value for s in next_statuses(current)]}"
        )


def next_statuses(current: ProjectStatus) -> list[ProjectStatus]:
    """The set of statuses legally reachable from ``current`` (single forward step)."""
    idx = _ORDER.index(current)
    return _ORDER[idx + 1 : idx + 2]


def validate_transition(current: ProjectStatus, requested: ProjectStatus) -> None:
    """Raise :class:`IllegalTransitionError` unless ``current → requested`` is legal."""
    if requested not in next_statuses(current):
        raise IllegalTransitionError(current, requested)


def is_terminal(status: ProjectStatus) -> bool:
    return status is ProjectStatus.RETIRED
