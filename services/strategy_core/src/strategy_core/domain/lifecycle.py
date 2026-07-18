"""Strategy lifecycle state machine.

The canonical forward path is:

    Draft → Configured → Validated → Paper Trading → Ready For Live → Live → Paused → Retired

with two operational edges beyond the straight line: ``Paused → Live`` (resume) and
``… → Retired`` (a strategy may always be retired from any active operational state). Retired
is terminal. Every transition is validated here and audited by the service layer; illegal
transitions are rejected (never silently applied).
"""

from __future__ import annotations

from enum import Enum


class StrategyStatus(str, Enum):
    DRAFT = "draft"
    CONFIGURED = "configured"
    VALIDATED = "validated"
    PAPER_TRADING = "paper_trading"
    READY_FOR_LIVE = "ready_for_live"
    LIVE = "live"
    PAUSED = "paused"
    RETIRED = "retired"


# Allowed transitions: current state -> set of permitted next states.
_TRANSITIONS: dict[StrategyStatus, frozenset[StrategyStatus]] = {
    StrategyStatus.DRAFT: frozenset({StrategyStatus.CONFIGURED}),
    StrategyStatus.CONFIGURED: frozenset({StrategyStatus.VALIDATED, StrategyStatus.RETIRED}),
    StrategyStatus.VALIDATED: frozenset({StrategyStatus.PAPER_TRADING, StrategyStatus.RETIRED}),
    StrategyStatus.PAPER_TRADING: frozenset(
        {StrategyStatus.READY_FOR_LIVE, StrategyStatus.PAUSED, StrategyStatus.RETIRED}
    ),
    StrategyStatus.READY_FOR_LIVE: frozenset(
        {StrategyStatus.LIVE, StrategyStatus.PAUSED, StrategyStatus.RETIRED}
    ),
    StrategyStatus.LIVE: frozenset({StrategyStatus.PAUSED, StrategyStatus.RETIRED}),
    StrategyStatus.PAUSED: frozenset(
        {StrategyStatus.LIVE, StrategyStatus.READY_FOR_LIVE, StrategyStatus.RETIRED}
    ),
    StrategyStatus.RETIRED: frozenset(),
}

# Statuses in which the strategy is immutable to configuration/metadata edits.
_IMMUTABLE = frozenset({StrategyStatus.RETIRED})


def can_transition(current: StrategyStatus, target: StrategyStatus) -> bool:
    return target in _TRANSITIONS.get(current, frozenset())


def allowed_transitions(current: StrategyStatus) -> list[StrategyStatus]:
    return sorted(_TRANSITIONS.get(current, frozenset()), key=lambda s: s.value)


def is_terminal(status: StrategyStatus) -> bool:
    return not _TRANSITIONS.get(status, frozenset())


def is_editable(status: StrategyStatus) -> bool:
    """Whether configuration/metadata may still be edited (a new version created)."""
    return status not in _IMMUTABLE
