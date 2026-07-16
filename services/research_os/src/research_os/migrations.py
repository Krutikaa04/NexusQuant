"""Ordered migration set for the research schema (SPEC-007 §5; SPEC-006 migration authority)."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncConnection

from nexus_platform.migrations.runner import Migration
from research_os.db.models import Base


async def _0001_create_research_schema(conn: AsyncConnection) -> None:
    """Create research_projects, hypotheses, experiments, research_reviews, status history."""
    await conn.run_sync(Base.metadata.create_all)


MIGRATIONS: list[Migration] = [
    Migration(
        id="0001_create_research_schema",
        description="research_projects, hypotheses, experiments, research_reviews, research_status_history",
        upgrade=_0001_create_research_schema,
    ),
]
