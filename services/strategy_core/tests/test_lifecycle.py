"""Unit tests for the lifecycle state machine (Strategy Studio)."""

from __future__ import annotations

from strategy_core.domain.lifecycle import (
    StrategyStatus,
    allowed_transitions,
    can_transition,
    is_editable,
    is_execution_ready,
    is_terminal,
)

S = StrategyStatus


def test_forward_path_is_allowed():
    chain = [
        (S.DRAFT, S.CONFIGURED),
        (S.CONFIGURED, S.VALIDATED),
        (S.VALIDATED, S.READY),
        (S.READY, S.PAUSED),
    ]
    for src, dst in chain:
        assert can_transition(src, dst)


def test_pause_resume_and_archive():
    assert can_transition(S.PAUSED, S.READY)          # resume
    assert can_transition(S.READY, S.ARCHIVED)
    assert can_transition(S.PAUSED, S.ARCHIVED)
    assert can_transition(S.DRAFT, S.ARCHIVED)         # archive from any active state


def test_illegal_transitions_rejected():
    assert not can_transition(S.DRAFT, S.READY)
    assert not can_transition(S.DRAFT, S.VALIDATED)
    assert not can_transition(S.CONFIGURED, S.READY)
    assert not can_transition(S.READY, S.DRAFT)


def test_archived_is_terminal_and_immutable():
    assert is_terminal(S.ARCHIVED)
    assert allowed_transitions(S.ARCHIVED) == []
    assert not is_editable(S.ARCHIVED)
    assert is_editable(S.DRAFT)
    assert is_editable(S.READY)


def test_execution_ready_only_when_ready():
    assert is_execution_ready(S.READY)
    for s in (S.DRAFT, S.CONFIGURED, S.VALIDATED, S.PAUSED, S.ARCHIVED):
        assert not is_execution_ready(s)
