"""Async engine and session factory.

A thin wrapper so the rest of the service depends on an injected ``sessionmaker`` rather
than a module-global engine, which keeps tests hermetic (each test gets its own in-memory
database) and honours dependency injection (SPEC engineering standards).
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

from event_fabric.db.models import Base


class Database:
    """Owns the async engine and session factory for a single service instance."""

    def __init__(self, url: str, *, echo: bool = False) -> None:
        # ``StaticPool`` is required for in-memory SQLite so every connection shares one
        # database; for Postgres the default pool is used.
        connect_args: dict = {}
        engine_kwargs: dict = {"echo": echo, "future": True}
        if url.startswith("sqlite+aiosqlite"):
            from sqlalchemy.pool import StaticPool

            connect_args = {"check_same_thread": False}
            engine_kwargs["poolclass"] = StaticPool
        self._engine: AsyncEngine = create_async_engine(
            url, connect_args=connect_args, **engine_kwargs
        )
        self._sessionmaker = async_sessionmaker(
            self._engine, expire_on_commit=False, class_=AsyncSession
        )

    @property
    def engine(self) -> AsyncEngine:
        return self._engine

    async def create_all(self) -> None:
        """Create the fabric's own tables (used for tests and first-run bootstrap)."""
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        async with self._sessionmaker() as session:
            yield session

    async def dispose(self) -> None:
        await self._engine.dispose()
