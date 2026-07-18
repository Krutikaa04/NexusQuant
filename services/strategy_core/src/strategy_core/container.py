"""Composition root for Strategy Core (dependency injection)."""

from __future__ import annotations

from dataclasses import dataclass, field

from nexus_platform.db.session import Database
from nexus_platform.migrations.runner import MigrationRunner
from strategy_core.config import Settings
from strategy_core.migrations import MIGRATIONS
from strategy_core.services.strategies import StrategyDashboardService, StrategyService


@dataclass
class Container:
    settings: Settings
    database: Database
    strategies: StrategyService
    dashboard: StrategyDashboardService
    applied_migrations: list[str] = field(default_factory=list)

    @classmethod
    def build(cls, settings: Settings) -> "Container":
        database = Database(settings.database_url, pool_size=settings.db_pool_size)
        return cls(
            settings=settings,
            database=database,
            strategies=StrategyService(database, settings),
            dashboard=StrategyDashboardService(database),
        )

    async def startup(self) -> None:
        report = await MigrationRunner(self.database.engine, MIGRATIONS).run()
        self.applied_migrations = report.applied + report.skipped

    async def shutdown(self) -> None:
        await self.database.dispose()
