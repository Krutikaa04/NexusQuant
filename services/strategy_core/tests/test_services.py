"""Service-layer tests: CRUD, versioning, lifecycle, rollback, clone, health, audit."""

from __future__ import annotations

import pytest

from strategy_core.domain.errors import (
    IllegalTransition,
    ImmutableStrategy,
    StrategyNotFound,
    ValidationError,
)
from strategy_core.domain.models import StrategyConfig


def sample_config() -> StrategyConfig:
    return StrategyConfig(
        symbols=["RELIANCE", "TCS"],
        exchanges=["NSE"],
        timeframes=["1m", "5m"],
        entry_params={"rsi_below": 30},
        exit_params={"rsi_above": 70},
        risk_params={"max_loss_pct": 2.0},
        position_sizing={"model": "fixed", "qty": 10},
        trading_session={"start": "09:15", "end": "15:30"},
    )


async def _create(container, **overrides):
    kwargs = dict(
        name="Mean Reversion NIFTY", description="RSI mean reversion",
        category="mean_reversion", owner="quant@nexus", tags=["nifty", "intraday"],
        config=sample_config(), actor="tester",
    )
    kwargs.update(overrides)
    return await container.strategies.create_strategy(**kwargs)


async def test_create_defaults_to_draft_v1_with_health(container):
    s = await _create(container)
    assert s["status"] == "draft"
    assert s["version"] == 1
    assert s["health"]["enabled"] is True
    assert s["health"]["trading_allowed"] is False
    assert s["configuration"]["symbols"] == ["RELIANCE", "TCS"]
    assert s["version_count"] == 1


async def test_create_requires_name(container):
    with pytest.raises(ValidationError):
        await _create(container, name="   ")


async def test_update_creates_new_immutable_version(container):
    s = await _create(container)
    updated = await container.strategies.update_strategy(
        s["id"], description="tuned", change_summary="tune", actor="tester"
    )
    assert updated["version"] == 2
    assert updated["version_count"] == 2
    versions = await container.strategies.list_versions(s["id"])
    # v1 snapshot is untouched (immutable history).
    v1 = next(v for v in versions if v["version"] == 1)
    assert v1["description"] == "RSI mean reversion"


async def test_config_update_versions_config(container):
    s = await _create(container)
    new_cfg = StrategyConfig(symbols=["INFY"], exchanges=["NSE"], timeframes=["15m"])
    updated = await container.strategies.update_strategy(
        s["id"], config=new_cfg, actor="tester"
    )
    assert updated["configuration"]["symbols"] == ["INFY"]


async def test_legal_transition_and_audit(container):
    s = await _create(container)
    moved = await container.strategies.transition(
        s["id"], to_status="configured", reason="ready", actor="tester"
    )
    assert moved["status"] == "configured"
    audit = await container.strategies.get_audit(s["id"])
    actions = [a["action"] for a in audit]
    assert "transition" in actions and "created" in actions


async def test_illegal_transition_rejected(container):
    s = await _create(container)
    with pytest.raises(IllegalTransition):
        await container.strategies.transition(s["id"], to_status="ready", actor="tester")


async def test_archived_is_immutable(container):
    s = await _create(container)
    for st in ("configured", "validated", "archived"):
        await container.strategies.transition(s["id"], to_status=st, actor="tester")
    with pytest.raises(ImmutableStrategy):
        await container.strategies.update_strategy(s["id"], description="x", actor="tester")


async def test_archive_helper_transitions_to_archived(container):
    s = await _create(container)
    archived = await container.strategies.archive(s["id"], actor="tester")
    assert archived["status"] == "archived"
    assert archived["is_terminal"] is True


async def test_rollback_creates_new_version_from_old(container):
    s = await _create(container)
    await container.strategies.update_strategy(
        s["id"], name="Renamed", actor="tester"
    )
    rolled = await container.strategies.rollback(s["id"], to_version=1, actor="tester")
    assert rolled["version"] == 3
    assert rolled["name"] == "Mean Reversion NIFTY"


async def test_clone_produces_independent_draft(container):
    s = await _create(container)
    await container.strategies.transition(s["id"], to_status="configured", actor="tester")
    clone = await container.strategies.clone_strategy(
        s["id"], new_name="Clone A", actor="tester"
    )
    assert clone["id"] != s["id"]
    assert clone["status"] == "draft"
    assert clone["version"] == 1
    assert clone["configuration"]["symbols"] == ["RELIANCE", "TCS"]


async def test_compare_versions_reports_changed_fields(container):
    s = await _create(container)
    await container.strategies.update_strategy(s["id"], name="V2 Name", actor="tester")
    cmp = await container.strategies.compare_versions(s["id"], 1, 2)
    assert "name" in cmp["changed_fields"]


async def test_soft_delete_hides_strategy(container):
    s = await _create(container)
    await container.strategies.soft_delete(s["id"], actor="tester")
    with pytest.raises(StrategyNotFound):
        await container.strategies.get_detail(s["id"])
    listing = await container.strategies.list_strategies()
    assert all(x["id"] != s["id"] for x in listing)


async def test_dashboard_summary_counts(container):
    a = await _create(container, name="A")
    await _create(container, name="B")
    await container.strategies.transition(a["id"], to_status="configured", actor="t")
    dash = await container.dashboard.summary()
    assert dash["total"] == 2
    assert dash["draft"] >= 1
    assert "by_status" in dash
    assert len(dash["recent"]) == 2
