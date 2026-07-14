"""FastAPI application entrypoint for the Data Platform (SPEC-006).

``create_app`` is a factory so tests can inject an in-memory database, cache, and event
publisher. The lifespan handler runs migrations on startup (the migration authority) and
disposes the engine on shutdown.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from nexus_platform.cache.base import AbstractCache
from data_platform.api.controller import router
from data_platform.config import Settings, get_settings
from data_platform.container import Container
from data_platform.events.publisher import EventPublisher

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def create_app(
    settings: Settings | None = None,
    *,
    cache: AbstractCache | None = None,
    publisher: EventPublisher | None = None,
) -> FastAPI:
    settings = settings or get_settings()
    container = Container.build(settings, cache=cache, publisher=publisher)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        await container.startup()
        yield
        await container.shutdown()

    app = FastAPI(
        title="NexusQuant — Data Platform & Knowledge Layer",
        version="0.1.0",
        summary="Canonical persistence, migrations, immutable artifacts (SPEC-006).",
        lifespan=lifespan,
    )
    app.state.container = container
    app.include_router(router)
    return app


app = create_app()
