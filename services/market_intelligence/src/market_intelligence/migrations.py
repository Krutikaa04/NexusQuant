"""Ordered migration set for the market schema (SPEC-004; SPEC-006 migration authority)."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncConnection

from nexus_platform.migrations.runner import Migration
from market_intelligence.db.models import Base


async def _0001_create_market_schema(conn: AsyncConnection) -> None:
    """Create instruments, ticks, candles, and data_quality tables."""
    await conn.run_sync(Base.metadata.create_all)


MIGRATIONS: list[Migration] = [
    Migration(
        id="0001_create_market_schema",
        description="instruments, ticks, candles, data_quality",
        upgrade=_0001_create_market_schema,
    ),
]
