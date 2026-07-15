"""Ordered migration set for the market schema (SPEC-004; SPEC-006 migration authority)."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncConnection

from nexus_platform.migrations.runner import Migration
from market_intelligence.db.models import Base


async def _0001_create_market_schema(conn: AsyncConnection) -> None:
    """Create instruments, ticks, candles, and data_quality tables."""
    await conn.run_sync(Base.metadata.create_all)


async def _0002_calendar_corp_actions_regimes(conn: AsyncConnection) -> None:
    """Create trading_holidays, special_sessions, corporate_actions, market_regimes.

    ``create_all`` is idempotent per-table, so it only creates the tables added since
    migration 0001.
    """
    await conn.run_sync(Base.metadata.create_all)


MIGRATIONS: list[Migration] = [
    Migration(
        id="0001_create_market_schema",
        description="instruments, ticks, candles, data_quality",
        upgrade=_0001_create_market_schema,
    ),
    Migration(
        id="0002_calendar_corp_actions_regimes",
        description="trading_holidays, special_sessions, corporate_actions, market_regimes",
        upgrade=_0002_calendar_corp_actions_regimes,
    ),
]
