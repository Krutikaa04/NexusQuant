"""Strategy lifecycle state machine (Strategy Studio).

Canonical path:

    Draft → Configured → Validated → Ready → Paused → Archived

with two operational edges beyond the straight line: ``Paused → Ready`` (resume) and
``… → Archived`` (a strategy may be archived from any non-archived state). Archived is
terminal and immutable. Every transition is validated here and audited by the service layer;
invalid transitions are rejected (never silently applied).
"""

from __future__ import annotations

from enum import Enum


class StrategyStatus(str, Enum):
    DRAFT = "draft"
    CONFIGURED = "configured"
    VALIDATED = "validated"
    READY = "ready"
    PAUSED = "paused"
    ARCHIVED = "archived"


# Allowed transitions: current state -> set of permitted next states.
_TRANSITIONS: dict[StrategyStatus, frozenset[StrategyStatus]] = {
    StrategyStatus.DRAFT: frozenset({StrategyStatus.CONFIGURED, StrategyStatus.ARCHIVED}),
    StrategyStatus.CONFIGURED: frozenset({StrategyStatus.VALIDATED, StrategyStatus.ARCHIVED}),
    StrategyStatus.VALIDATED: frozenset({StrategyStatus.READY, StrategyStatus.ARCHIVED}),
    StrategyStatus.READY: frozenset({StrategyStatus.PAUSED, StrategyStatus.ARCHIVED}),
    StrategyStatus.PAUSED: frozenset({StrategyStatus.READY, StrategyStatus.ARCHIVED}),
    StrategyStatus.ARCHIVED: frozenset(),
}

# Statuses in which the strategy is immutable to configuration/metadata edits.
_IMMUTABLE = frozenset({StrategyStatus.ARCHIVED})

# A strategy is execution-ready only when it has reached READY.
_EXECUTION_READY = frozenset({StrategyStatus.READY})


def can_transition(current: StrategyStatus, target: StrategyStatus) -> bool:
    return target in _TRANSITIONS.get(current, frozenset())


def allowed_transitions(current: StrategyStatus) -> list[StrategyStatus]:
    return sorted(_TRANSITIONS.get(current, frozenset()), key=lambda s: s.value)


def is_terminal(status: StrategyStatus) -> bool:
    return not _TRANSITIONS.get(status, frozenset())


def is_editable(status: StrategyStatus) -> bool:
    """Whether configuration/metadata may still be edited (a new version created)."""
    return status not in _IMMUTABLE


def is_execution_ready(status: StrategyStatus) -> bool:
    return status in _EXECUTION_READY
