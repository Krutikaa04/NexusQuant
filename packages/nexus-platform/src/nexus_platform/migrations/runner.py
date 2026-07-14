"""A small, reproducible, audited migration runner (SPEC-006 §15 step 1, §11).

Design goals from the spec:
* **Reproducible** — migrations are an *ordered* list applied exactly once, in order.
* **Audited** — every applied migration is recorded (id, checksum, timestamp) in a
  bookkeeping table so the applied history is inspectable.
* **Drift-detecting** — a migration whose definition changed after being applied is a
  reproducibility violation and is rejected on the next run (checksum mismatch).

Migrations are ordinary Python objects carrying an ``upgrade`` coroutine that receives a
raw :class:`AsyncConnection`. This keeps the runner backend-agnostic (SQLite and Postgres)
and lets a migration create tables via SQLAlchemy metadata or execute explicit DDL.
"""

from __future__ import annotations

import hashlib
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine

logger = logging.getLogger(__name__)

Upgrade = Callable[[AsyncConnection], Awaitable[None]]

_BOOKKEEPING_DDL = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    id            VARCHAR(128) PRIMARY KEY,
    checksum      VARCHAR(64)  NOT NULL,
    description   VARCHAR(512) NOT NULL,
    applied_at    TIMESTAMP    NOT NULL
)
"""


@dataclass(frozen=True)
class Migration:
    """A single, ordered schema change.

    ``id`` must sort in application order (e.g. ``"0001_initial"``). ``checksum`` is derived
    from the id + description so that editing an already-applied migration is detected.
    """

    id: str
    description: str
    upgrade: Upgrade = field(repr=False)

    @property
    def checksum(self) -> str:
        return hashlib.sha256(f"{self.id}:{self.description}".encode()).hexdigest()


@dataclass(frozen=True, slots=True)
class MigrationReport:
    applied: list[str]
    skipped: list[str]


class MigrationDriftError(RuntimeError):
    """Raised when a previously-applied migration's checksum no longer matches its definition."""


class MigrationRunner:
    def __init__(self, engine: AsyncEngine, migrations: list[Migration]) -> None:
        # Enforce a strict, stable order; duplicate ids are a programming error.
        ids = [m.id for m in migrations]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate migration ids")
        self._engine = engine
        self._migrations = sorted(migrations, key=lambda m: m.id)

    async def _applied(self, conn: AsyncConnection) -> dict[str, str]:
        rows = (await conn.execute(text("SELECT id, checksum FROM schema_migrations"))).all()
        return {row.id: row.checksum for row in rows}

    async def run(self) -> MigrationReport:
        """Apply all pending migrations in order. Idempotent and drift-checked."""
        applied: list[str] = []
        skipped: list[str] = []
        async with self._engine.begin() as conn:
            await conn.execute(text(_BOOKKEEPING_DDL))
            already = await self._applied(conn)

        for migration in self._migrations:
            existing = already.get(migration.id)
            if existing is not None:
                if existing != migration.checksum:
                    raise MigrationDriftError(
                        f"migration '{migration.id}' was modified after being applied"
                    )
                skipped.append(migration.id)
                continue

            # Each migration runs in its own transaction so a failure leaves earlier
            # migrations committed and this one fully rolled back.
            async with self._engine.begin() as conn:
                await migration.upgrade(conn)
                await conn.execute(
                    text(
                        "INSERT INTO schema_migrations (id, checksum, description, applied_at) "
                        "VALUES (:id, :checksum, :description, :applied_at)"
                    ),
                    {
                        "id": migration.id,
                        "checksum": migration.checksum,
                        "description": migration.description,
                        # ISO-8601 string is portable across SQLite and Postgres and avoids
                        # the deprecated sqlite datetime adapter (Python 3.12+).
                        "applied_at": datetime.now(timezone.utc).isoformat(),
                    },
                )
            logger.info("applied migration %s — %s", migration.id, migration.description)
            applied.append(migration.id)

        return MigrationReport(applied=applied, skipped=skipped)
