"""Repositories for the strategy aggregate. SQL lives only here (SPEC-006 §15)."""

from __future__ import annotations

from sqlalchemy import func, select

from nexus_platform.db.repository import BaseRepository
from strategy_core.db.models import (
    StrategyHealthRecord,
    StrategyRecord,
    StrategyVersionRecord,
)


class StrategyRepository(BaseRepository[StrategyRecord]):
    model = StrategyRecord

    async def get_active(self, strategy_id: str) -> StrategyRecord | None:
        """Fetch a strategy that has not been soft-deleted."""
        row = await self.session.get(StrategyRecord, strategy_id)
        if row is None or row.deleted_at is not None:
            return None
        return row

    async def list_filtered(
        self,
        *,
        status: str | None = None,
        category: str | None = None,
        owner: str | None = None,
        tag: str | None = None,
        include_deleted: bool = False,
    ) -> list[StrategyRecord]:
        stmt = select(StrategyRecord)
        if not include_deleted:
            stmt = stmt.where(StrategyRecord.deleted_at.is_(None))
        if status:
            stmt = stmt.where(StrategyRecord.status == status)
        if category:
            stmt = stmt.where(StrategyRecord.category == category)
        if owner:
            stmt = stmt.where(StrategyRecord.owner == owner)
        stmt = stmt.order_by(StrategyRecord.updated_at.desc())
        rows = list((await self.session.execute(stmt)).scalars().all())
        if tag:
            rows = [r for r in rows if tag in (r.tags or [])]
        return rows

    async def count_by_status(self) -> dict[str, int]:
        stmt = (
            select(StrategyRecord.status, func.count())
            .where(StrategyRecord.deleted_at.is_(None))
            .group_by(StrategyRecord.status)
        )
        rows = (await self.session.execute(stmt)).all()
        return {row[0]: int(row[1]) for row in rows}

    async def recent(self, limit: int = 6) -> list[StrategyRecord]:
        stmt = (
            select(StrategyRecord)
            .where(StrategyRecord.deleted_at.is_(None))
            .order_by(StrategyRecord.updated_at.desc())
            .limit(limit)
        )
        return list((await self.session.execute(stmt)).scalars().all())


class StrategyVersionRepository(BaseRepository[StrategyVersionRecord]):
    model = StrategyVersionRecord

    async def list_for(self, strategy_id: str) -> list[StrategyVersionRecord]:
        stmt = (
            select(StrategyVersionRecord)
            .where(StrategyVersionRecord.strategy_id == strategy_id)
            .order_by(StrategyVersionRecord.version.desc())
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def get_version(
        self, strategy_id: str, version: int
    ) -> StrategyVersionRecord | None:
        stmt = select(StrategyVersionRecord).where(
            StrategyVersionRecord.strategy_id == strategy_id,
            StrategyVersionRecord.version == version,
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()


class StrategyHealthRepository(BaseRepository[StrategyHealthRecord]):
    model = StrategyHealthRecord

    async def get_for(self, strategy_id: str) -> StrategyHealthRecord | None:
        return await self.session.get(StrategyHealthRecord, strategy_id)
