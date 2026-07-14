"""Migration runner tests: ordering, idempotency, audit, drift detection (SPEC-006 §15)."""

from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from nexus_platform.migrations.runner import (
    Migration,
    MigrationDriftError,
    MigrationRunner,
)


@pytest.fixture
def engine():
    from sqlalchemy.pool import StaticPool

    return create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


async def _create_widgets(conn) -> None:
    await conn.execute(text("CREATE TABLE widgets (id INTEGER PRIMARY KEY)"))


async def _create_gadgets(conn) -> None:
    await conn.execute(text("CREATE TABLE gadgets (id INTEGER PRIMARY KEY)"))


async def test_applies_in_order_and_records_audit(engine) -> None:
    runner = MigrationRunner(
        engine,
        [
            Migration("0002_gadgets", "gadgets", _create_gadgets),
            Migration("0001_widgets", "widgets", _create_widgets),
        ],
    )
    report = await runner.run()
    assert report.applied == ["0001_widgets", "0002_gadgets"]  # sorted, not input order
    async with engine.begin() as conn:
        rows = (await conn.execute(text("SELECT id FROM schema_migrations ORDER BY id"))).all()
    assert [r.id for r in rows] == ["0001_widgets", "0002_gadgets"]


async def test_idempotent_second_run_skips(engine) -> None:
    migrations = [Migration("0001_widgets", "widgets", _create_widgets)]
    await MigrationRunner(engine, migrations).run()
    report = await MigrationRunner(engine, migrations).run()
    assert report.applied == []
    assert report.skipped == ["0001_widgets"]


async def test_drift_is_rejected(engine) -> None:
    await MigrationRunner(engine, [Migration("0001", "original", _create_widgets)]).run()
    with pytest.raises(MigrationDriftError):
        # same id, different description => checksum mismatch => reproducibility violation
        await MigrationRunner(engine, [Migration("0001", "tampered", _create_widgets)]).run()


async def test_duplicate_ids_rejected(engine) -> None:
    with pytest.raises(ValueError):
        MigrationRunner(
            engine,
            [Migration("0001", "a", _create_widgets), Migration("0001", "b", _create_gadgets)],
        )
