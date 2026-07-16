"""Lifecycle state-machine unit tests (SPEC-007 §4, §12)."""

from __future__ import annotations

import pytest

from research_os.domain.lifecycle import (
    IllegalTransitionError,
    ProjectStatus,
    is_terminal,
    next_statuses,
    validate_transition,
)

CHAIN = [
    ProjectStatus.DRAFT,
    ProjectStatus.ACTIVE,
    ProjectStatus.EXPERIMENTING,
    ProjectStatus.VALIDATED,
    ProjectStatus.PAPER_TRADING,
    ProjectStatus.PRODUCTION_CANDIDATE,
    ProjectStatus.APPROVED,
    ProjectStatus.RETIRED,
]


def test_every_forward_step_is_legal() -> None:
    for current, nxt in zip(CHAIN, CHAIN[1:]):
        validate_transition(current, nxt)  # must not raise


def test_skipping_a_stage_is_illegal() -> None:
    with pytest.raises(IllegalTransitionError):
        validate_transition(ProjectStatus.DRAFT, ProjectStatus.EXPERIMENTING)
    with pytest.raises(IllegalTransitionError):
        validate_transition(ProjectStatus.ACTIVE, ProjectStatus.APPROVED)


def test_backward_transitions_are_illegal() -> None:
    for current, nxt in zip(CHAIN, CHAIN[1:]):
        with pytest.raises(IllegalTransitionError):
            validate_transition(nxt, current)


def test_self_transition_is_illegal() -> None:
    for status in CHAIN:
        with pytest.raises(IllegalTransitionError):
            validate_transition(status, status)


def test_retired_is_terminal() -> None:
    assert is_terminal(ProjectStatus.RETIRED)
    assert next_statuses(ProjectStatus.RETIRED) == []


def test_error_message_names_the_allowed_next_step() -> None:
    with pytest.raises(IllegalTransitionError, match="active"):
        validate_transition(ProjectStatus.DRAFT, ProjectStatus.RETIRED)
