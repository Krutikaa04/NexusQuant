"""Append-only audit repository."""

from __future__ import annotations

from sqlalchemy import select

from nexus_platform.db.repository import BaseRepository
from strategy_core.db.models import StrategyAuditRecord


class StrategyAuditRepository(BaseRepository[StrategyAuditRecord]):
    model = StrategyAuditRecord

    async def list_for(
        self, strategy_id: str, *, limit: int = 200
    ) -> list[StrategyAuditRecord]:
        stmt = (
            select(StrategyAuditRecord)
            .where(StrategyAuditRecord.strategy_id == strategy_id)
            .order_by(StrategyAuditRecord.id.desc())
            .limit(limit)
        )
        return list((await self.session.execute(stmt)).scalars().all())
