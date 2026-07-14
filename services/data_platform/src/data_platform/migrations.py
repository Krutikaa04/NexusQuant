"""Ordered migration set for the Data Platform (SPEC-006 §15 step 1).

Migrations are the *only* way schema comes into existence — the service never calls
``create_all`` at runtime. Each migration is reproducible and audited by the shared
:class:`~nexus_platform.migrations.runner.MigrationRunner`.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncConnection

from nexus_platform.migrations.runner import Migration
from data_platform.db.models import Base


async def _0001_create_artifact_store(conn: AsyncConnection) -> None:
    """Create the immutable artifact store, lineage, and read-model tables."""
    await conn.run_sync(Base.metadata.create_all)


MIGRATIONS: list[Migration] = [
    Migration(
        id="0001_create_artifact_store",
        description="artifacts, artifact_versions, lineage_edges, read_models",
        upgrade=_0001_create_artifact_store,
    ),
]
