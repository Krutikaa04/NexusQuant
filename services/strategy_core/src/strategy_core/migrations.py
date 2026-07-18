"""Ordered migration set for the strategy schema."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncConnection

from nexus_platform.migrations.runner import Migration
from strategy_core.db.models import Base


async def _0001_create_strategy_schema(conn: AsyncConnection) -> None:
    """Create strategies, strategy_versions, strategy_audit, strategy_health tables."""
    await conn.run_sync(Base.metadata.create_all)


MIGRATIONS: list[Migration] = [
    Migration(
        id="0001_create_strategy_schema",
        description="strategies, strategy_versions, strategy_audit, strategy_health",
        upgrade=_0001_create_strategy_schema,
    ),
]
