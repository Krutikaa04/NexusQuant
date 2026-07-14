"""Repository over materialised read models (SPEC-006 §2, §7 ReadModelUpdated)."""

from __future__ import annotations

from sqlalchemy import select

from nexus_platform.db.repository import BaseRepository
from nexus_shared.primitives.time import utc_now
from data_platform.db.models import ReadModel


class ReadModelRepository(BaseRepository[ReadModel]):
    model = ReadModel

    async def upsert(self, key: str, kind: str, projection: dict) -> ReadModel:
        existing = await self.session.get(ReadModel, key)
        if existing is None:
            record = ReadModel(
                key=key, kind=kind, projection=projection, revision=1, updated_at=utc_now()
            )
            self.session.add(record)
            await self.session.flush()
            return record
        existing.projection = projection
        existing.revision += 1
        existing.updated_at = utc_now()
        await self.session.flush()
        return existing

    async def get(self, key: str) -> ReadModel | None:  # type: ignore[override]
        return await self.session.get(ReadModel, key)

    async def list_by_kind(self, kind: str) -> list[ReadModel]:
        stmt = select(ReadModel).where(ReadModel.kind == kind)
        return list((await self.session.execute(stmt)).scalars().all())
