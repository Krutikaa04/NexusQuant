"""Test fixtures: an isolated in-memory Strategy Core container."""

from __future__ import annotations

import pytest
import pytest_asyncio

from strategy_core.config import Settings
from strategy_core.container import Container
from strategy_core.domain.models import StrategyConfig


@pytest.fixture
def settings() -> Settings:
    return Settings(
        STRATEGY_DATABASE_URL="sqlite+aiosqlite:///:memory:",
        auth_enabled=False,
    )


@pytest_asyncio.fixture
async def container(settings) -> Container:
    c = Container.build(settings)
    await c.startup()
    try:
        yield c
    finally:
        await c.shutdown()


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
