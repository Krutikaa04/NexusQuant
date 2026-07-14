"""Data-quality snapshot store (SPEC-004 Data Quality Engine)."""

from __future__ import annotations

from sqlalchemy import select

from nexus_platform.db.repository import BaseRepository
from nexus_shared.primitives.time import utc_now
from market_intelligence.db.models import DataQualityRecord
from market_intelligence.domain.quality import QualitySnapshot


class DataQualityRepository(BaseRepository[DataQualityRecord]):
    model = DataQualityRecord

    async def append(self, snapshot: QualitySnapshot) -> None:
        self.session.add(
            DataQualityRecord(
                symbol=snapshot.symbol,
                score=snapshot.score,
                confidence=snapshot.confidence.value,
                readiness=snapshot.readiness.value,
                metrics=snapshot.metrics,
                created_at=utc_now(),
            )
        )

    async def latest(self, symbol: str) -> DataQualityRecord | None:
        stmt = (
            select(DataQualityRecord)
            .where(DataQualityRecord.symbol == symbol)
            .order_by(DataQualityRecord.created_at.desc())
            .limit(1)
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()
