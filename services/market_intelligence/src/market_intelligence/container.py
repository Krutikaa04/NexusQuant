"""Composition root for Market Intelligence (dependency injection)."""

from __future__ import annotations

from dataclasses import dataclass, field

from nexus_shared.events.publisher import (
    EventPublisher,
    HttpFabricPublisher,
    InMemoryEventPublisher,
)
from nexus_platform.db.session import Database
from nexus_platform.migrations.runner import MigrationRunner
from market_intelligence.config import Settings
from market_intelligence.domain.candles import Interval
from market_intelligence.events.schemas import register_published_schemas
from market_intelligence.ingestion.pipeline import IngestionPipeline
from market_intelligence.ingestion.quality import DataQualityEngine
from market_intelligence.ingestion.validator import TickValidator
from market_intelligence.migrations import MIGRATIONS
from market_intelligence.services.instruments import InstrumentService
from market_intelligence.services.queries import MarketQueryService
from market_intelligence.services.replay import ReplayService


def _build_publisher(settings: Settings) -> EventPublisher:
    if settings.event_fabric_url:
        return HttpFabricPublisher(settings.event_fabric_url)
    return InMemoryEventPublisher()


@dataclass
class Container:
    settings: Settings
    database: Database
    publisher: EventPublisher
    pipeline: IngestionPipeline
    instruments: InstrumentService
    replay: ReplayService
    queries: MarketQueryService
    applied_migrations: list[str] = field(default_factory=list)

    @classmethod
    def build(
        cls, settings: Settings, *, publisher: EventPublisher | None = None
    ) -> "Container":
        register_published_schemas()
        database = Database(settings.database_url, pool_size=settings.db_pool_size)
        publisher = publisher or _build_publisher(settings)
        pipeline = IngestionPipeline(
            database,
            publisher,
            interval=Interval(settings.default_candle_interval_seconds),
            validator=TickValidator(max_drift_ms=settings.dq_max_timestamp_drift_ms),
            quality=DataQualityEngine(
                window_size=settings.dq_window_size,
                max_drift_ms=settings.dq_max_timestamp_drift_ms,
                ready_threshold=settings.dq_ready_threshold,
                degraded_threshold=settings.dq_degraded_threshold,
            ),
        )
        instruments = InstrumentService(database, publisher, pipeline)
        replay = ReplayService(database, publisher)
        queries = MarketQueryService(database)
        return cls(
            settings=settings,
            database=database,
            publisher=publisher,
            pipeline=pipeline,
            instruments=instruments,
            replay=replay,
            queries=queries,
        )

    async def startup(self) -> None:
        report = await MigrationRunner(self.database.engine, MIGRATIONS).run()
        self.applied_migrations = report.applied + report.skipped
        # Prime the pipeline's known-symbol set from any persisted instruments.
        await self.instruments.load_known_symbols()

    async def shutdown(self) -> None:
        await self.database.dispose()
