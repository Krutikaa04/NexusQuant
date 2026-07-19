"""Seed a small demo set of strategies through the real Strategy Core services.

Every strategy below is created via the actual StrategyService (create → transition), so the
dashboard, lifecycle timelines, version history and audit logs all reflect genuine service
behaviour — nothing is inserted directly into the database.
"""

from __future__ import annotations

import logging

from strategy_core.container import Container
from strategy_core.domain.models import StrategyConfig

logger = logging.getLogger("nexus.backend.seed_strategies")

# (name, category, description, tags, config, lifecycle path to walk after creation)
_DEMO: list[dict] = [
    {
        "name": "NIFTY Mean Reversion",
        "category": "mean_reversion",
        "description": "RSI-based intraday mean reversion on large-cap NSE equities.",
        "tags": ["intraday", "rsi", "nifty50"],
        "config": StrategyConfig(
            symbols=["RELIANCE", "TCS", "INFY"], exchanges=["NSE"],
            timeframes=["1m", "5m"], entry_params={"rsi_below": 30},
            exit_params={"rsi_above": 65}, risk_params={"max_loss_pct": 1.5, "max_positions": 3},
            position_sizing={"model": "fixed_qty", "qty": 25},
            trading_session={"start": "09:20", "end": "15:15"},
        ),
        "path": ["configured", "validated"],
    },
    {
        "name": "Bank Momentum Breakout",
        "category": "momentum",
        "description": "Opening-range breakout on banking names with trailing exits.",
        "tags": ["breakout", "banking"],
        "config": StrategyConfig(
            symbols=["HDFCBANK", "ICICIBANK", "SBIN"], exchanges=["NSE"],
            timeframes=["5m"], entry_params={"breakout_window": 15},
            exit_params={"trail_pct": 0.8}, risk_params={"max_loss_pct": 2.0},
            position_sizing={"model": "risk_pct", "risk_pct": 0.5},
            trading_session={"start": "09:15", "end": "15:00"},
        ),
        "path": ["configured", "validated", "ready"],
    },
    {
        "name": "Pairs: RELIANCE / ONGC",
        "category": "stat_arb",
        "description": "Cointegration-based statistical arbitrage pair trade.",
        "tags": ["pairs", "stat-arb"],
        "config": StrategyConfig(
            symbols=["RELIANCE", "ONGC"], exchanges=["NSE"], timeframes=["15m"],
            entry_params={"zscore": 2.0}, exit_params={"zscore": 0.5},
            risk_params={"max_loss_pct": 3.0},
            position_sizing={"model": "notional", "notional": 200000},
            trading_session={"start": "09:30", "end": "15:00"},
        ),
        "path": ["configured", "validated", "ready", "paused"],
    },
    {
        "name": "Overnight Gap Fade (draft)",
        "category": "mean_reversion",
        "description": "Fade large overnight gaps on the open. Still being configured.",
        "tags": ["gap", "draft"],
        "config": StrategyConfig(
            symbols=["TCS"], exchanges=["NSE"], timeframes=["1m"],
            entry_params={"gap_pct": 1.5},
        ),
        "path": [],
    },
]


async def seed_strategies(container: Container) -> None:
    existing = await container.strategies.list_strategies()
    if existing:
        logger.info("strategies already seeded (%d present); skipping", len(existing))
        return
    for spec in _DEMO:
        created = await container.strategies.create_strategy(
            name=spec["name"], description=spec["description"], category=spec["category"],
            owner="demo@nexus", tags=spec["tags"], config=spec["config"], actor="seed",
        )
        for step in spec["path"]:
            await container.strategies.transition(
                created["id"], to_status=step, reason="demo seed", actor="seed"
            )
    logger.info("seeded %d demo strategies", len(_DEMO))
