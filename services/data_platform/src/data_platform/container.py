"""Composition root for the Data Platform (dependency injection).

Selects concrete adapters from configuration — in-memory vs Redis cache, in-memory vs HTTP
event publisher — and wires the migration authority, repositories-backed services, and the
schema registrations. On startup it runs migrations (the only path to schema existence).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from nexus_platform.cache.base import AbstractCache
from nexus_platform.cache.memory import InMemoryCache
from nexus_platform.db.session import Database
from nexus_platform.migrations.runner import MigrationReport, MigrationRunner
from data_platform.config import Settings
from data_platform.events.publisher import (
    EventPublisher,
    HttpFabricPublisher,
    InMemoryEventPublisher,
)
from data_platform.events.schemas import register_consumed_schemas
from data_platform.migrations import MIGRATIONS
from data_platform.services.indexing import IndexingService
from data_platform.services.queries import QueryService


def _build_cache(settings: Settings) -> AbstractCache:
    if settings.redis_url:
        from nexus_platform.cache.redis import RedisCache

        return RedisCache(settings.redis_url)
    return InMemoryCache()


def _build_publisher(settings: Settings) -> EventPublisher:
    if settings.event_fabric_url:
        return HttpFabricPublisher(settings.event_fabric_url)
    return InMemoryEventPublisher()


@dataclass
class Container:
    settings: Settings
    database: Database
    cache: AbstractCache
    publisher: EventPublisher
    indexing: IndexingService
    queries: QueryService
    applied_migrations: list[str] = field(default_factory=list)

    @classmethod
    def build(
        cls,
        settings: Settings,
        *,
        cache: AbstractCache | None = None,
        publisher: EventPublisher | None = None,
    ) -> "Container":
        register_consumed_schemas()
        database = Database(settings.database_url, pool_size=settings.db_pool_size)
        cache = cache or _build_cache(settings)
        publisher = publisher or _build_publisher(settings)
        indexing = IndexingService(database, publisher, cache)
        queries = QueryService(database, cache, ttl=settings.cache_ttl)
        return cls(
            settings=settings,
            database=database,
            cache=cache,
            publisher=publisher,
            indexing=indexing,
            queries=queries,
        )

    async def startup(self) -> MigrationReport:
        report = await MigrationRunner(self.database.engine, MIGRATIONS).run()
        self.applied_migrations = report.applied + report.skipped
        return report

    async def shutdown(self) -> None:
        await self.database.dispose()
