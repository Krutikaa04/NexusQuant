"""Generic async repository base (SPEC-006 §15: SQL lives only inside repositories).

A thin, typed convenience layer over an :class:`AsyncSession`. Concrete repositories
subclass this, add their query methods, and remain the single place ORM/SQL is used —
callers deal in domain objects, never in SQL.
"""

from __future__ import annotations

from typing import Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

ModelT = TypeVar("ModelT")


class BaseRepository(Generic[ModelT]):
    model: type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, entity: ModelT) -> ModelT:
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def get(self, pk) -> ModelT | None:
        return await self.session.get(self.model, pk)

    async def count(self) -> int:
        stmt = select(func.count()).select_from(self.model)
        return int((await self.session.execute(stmt)).scalar_one())

    async def list_all(self, *, limit: int | None = None, offset: int = 0) -> list[ModelT]:
        stmt = select(self.model).offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)
        return list((await self.session.execute(stmt)).scalars().all())
