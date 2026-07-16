"""Composition root for the Research OS (dependency injection)."""

from __future__ import annotations

from dataclasses import dataclass, field

from nexus_shared.events.publisher import (
    EventPublisher,
    HttpFabricPublisher,
    InMemoryEventPublisher,
)
from nexus_platform.db.session import Database
from nexus_platform.migrations.runner import MigrationRunner
from research_os.config import Settings
from research_os.events.schemas import register_published_schemas
from research_os.migrations import MIGRATIONS
from research_os.services.dashboard import DashboardService
from research_os.services.experiments import ExperimentService
from research_os.services.hypotheses import HypothesisService
from research_os.services.projects import ProjectService
from research_os.services.reviews import ReviewService


def _build_publisher(settings: Settings) -> EventPublisher:
    if settings.event_fabric_url:
        return HttpFabricPublisher(settings.event_fabric_url)
    return InMemoryEventPublisher()


@dataclass
class Container:
    settings: Settings
    database: Database
    publisher: EventPublisher
    projects: ProjectService
    hypotheses: HypothesisService
    experiments: ExperimentService
    reviews: ReviewService
    dashboard: DashboardService
    applied_migrations: list[str] = field(default_factory=list)

    @classmethod
    def build(
        cls, settings: Settings, *, publisher: EventPublisher | None = None
    ) -> "Container":
        register_published_schemas()
        database = Database(settings.database_url, pool_size=settings.db_pool_size)
        publisher = publisher or _build_publisher(settings)
        return cls(
            settings=settings,
            database=database,
            publisher=publisher,
            projects=ProjectService(database, publisher, settings),
            hypotheses=HypothesisService(database, publisher),
            experiments=ExperimentService(database, publisher),
            reviews=ReviewService(database, publisher),
            dashboard=DashboardService(database),
        )

    async def startup(self) -> None:
        report = await MigrationRunner(self.database.engine, MIGRATIONS).run()
        self.applied_migrations = report.applied + report.skipped

    async def shutdown(self) -> None:
        await self.database.dispose()
