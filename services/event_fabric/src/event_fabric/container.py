"""Composition root (dependency injection).

Constructs and wires the fabric's singletons — database, schema registry, subscription
registry, WebSocket gateway, publisher and replay service — in one place. FastAPI stores
the container on ``app.state`` and request handlers receive collaborators via ``Depends``,
so no module reaches for a global singleton (SPEC engineering standards: DI, testability).
"""

from __future__ import annotations

from dataclasses import dataclass

from nexus_shared.events.registry import SchemaRegistry, default_registry
from event_fabric.config import Settings
from event_fabric.db.session import Database
from event_fabric.services.publisher import Publisher
from event_fabric.services.replay import ReplayService
from event_fabric.services.subscriber import SubscriptionRegistry
from event_fabric.ws.gateway import WebSocketGateway


@dataclass
class Container:
    settings: Settings
    database: Database
    registry: SchemaRegistry
    subscriptions: SubscriptionRegistry
    gateway: WebSocketGateway
    publisher: Publisher
    replay: ReplayService

    @classmethod
    def build(
        cls, settings: Settings, *, registry: SchemaRegistry | None = None
    ) -> "Container":
        database = Database(settings.database_url)
        reg = registry or default_registry
        # honour the configured strict/lenient policy on the shared registry instance
        reg._strict = settings.strict_schema_validation  # noqa: SLF001 - intentional policy wiring
        subscriptions = SubscriptionRegistry()
        gateway = WebSocketGateway()
        publisher = Publisher(
            database,
            reg,
            subscriptions,
            signing_key=settings.event_signing_key,
            stream_sink=gateway,
        )
        replay = ReplayService(database, subscriptions, batch_size=settings.replay_batch_size)
        return cls(
            settings=settings,
            database=database,
            registry=reg,
            subscriptions=subscriptions,
            gateway=gateway,
            publisher=publisher,
            replay=replay,
        )

    async def startup(self) -> None:
        await self.database.create_all()

    async def shutdown(self) -> None:
        await self.database.dispose()
