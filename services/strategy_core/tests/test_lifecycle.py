"""Unit tests for the lifecycle state machine."""

from __future__ import annotations

from strategy_core.domain.lifecycle import (
    StrategyStatus,
    allowed_transitions,
    can_transition,
    is_editable,
    is_terminal,
)

S = StrategyStatus


def test_forward_path_is_allowed():
    chain = [
        (S.DRAFT, S.CONFIGURED),
        (S.CONFIGURED, S.VALIDATED),
        (S.VALIDATED, S.PAPER_TRADING),
        (S.PAPER_TRADING, S.READY_FOR_LIVE),
        (S.READY_FOR_LIVE, S.LIVE),
        (S.LIVE, S.PAUSED),
    ]
    for src, dst in chain:
        assert can_transition(src, dst)


def test_pause_resume_and_retire():
    assert can_transition(S.PAUSED, S.LIVE)
    assert can_transition(S.LIVE, S.RETIRED)
    assert can_transition(S.PAUSED, S.RETIRED)


def test_illegal_transitions_rejected():
    assert not can_transition(S.DRAFT, S.LIVE)
    assert not can_transition(S.DRAFT, S.VALIDATED)
    assert not can_transition(S.CONFIGURED, S.PAPER_TRADING)
    assert not can_transition(S.LIVE, S.DRAFT)


def test_retired_is_terminal_and_immutable():
    assert is_terminal(S.RETIRED)
    assert allowed_transitions(S.RETIRED) == []
    assert not is_editable(S.RETIRED)
    assert is_editable(S.DRAFT)
    assert is_editable(S.LIVE)
