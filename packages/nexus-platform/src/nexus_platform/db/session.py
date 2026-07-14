"""Async engine and session factory, shared by every service.

Depends on an injected DSN rather than a module global so each service instance — and each
test — owns an isolated engine. In-memory SQLite uses ``StaticPool`` so all sessions share
one database; Postgres uses the default pool with a configurable size.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


class Database:
    def __init__(self, url: str, *, echo: bool = False, pool_size: int | None = None) -> None:
        connect_args: dict = {}
        engine_kwargs: dict = {"echo": echo, "future": True}
        if url.startswith("sqlite+aiosqlite"):
            from sqlalchemy.pool import StaticPool

            connect_args = {"check_same_thread": False}
            engine_kwargs["poolclass"] = StaticPool
        elif pool_size is not None:
            engine_kwargs["pool_size"] = pool_size
        self._engine: AsyncEngine = create_async_engine(
            url, connect_args=connect_args, **engine_kwargs
        )
        self._sessionmaker = async_sessionmaker(
            self._engine, expire_on_commit=False, class_=AsyncSession
        )

    @property
    def engine(self) -> AsyncEngine:
        return self._engine

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        async with self._sessionmaker() as session:
            yield session

    @asynccontextmanager
    async def begin(self) -> AsyncIterator[AsyncSession]:
        """A session wrapped in a transaction that commits on success, rolls back on error."""
        async with self._sessionmaker() as session:
            async with session.begin():
                yield session

    async def dispose(self) -> None:
        await self._engine.dispose()
