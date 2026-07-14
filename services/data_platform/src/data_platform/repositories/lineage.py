"""Repository over the data-lineage DAG (SPEC-006 §2)."""

from __future__ import annotations

from uuid import uuid4

from sqlalchemy import select

from nexus_platform.db.repository import BaseRepository
from nexus_shared.primitives.time import utc_now
from data_platform.db.models import LineageEdge


class LineageRepository(BaseRepository[LineageEdge]):
    model = LineageEdge

    async def add_edge(
        self, upstream_version_id: str, downstream_version_id: str, relation: str = "derived_from"
    ) -> LineageEdge:
        edge = LineageEdge(
            id=str(uuid4()),
            upstream_version_id=upstream_version_id,
            downstream_version_id=downstream_version_id,
            relation=relation,
            created_at=utc_now(),
        )
        return await self.add(edge)

    async def upstream_of(self, version_id: str) -> list[LineageEdge]:
        stmt = select(LineageEdge).where(LineageEdge.downstream_version_id == version_id)
        return list((await self.session.execute(stmt)).scalars().all())

    async def downstream_of(self, version_id: str) -> list[LineageEdge]:
        stmt = select(LineageEdge).where(LineageEdge.upstream_version_id == version_id)
        return list((await self.session.execute(stmt)).scalars().all())
