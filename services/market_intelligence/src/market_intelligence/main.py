"""FastAPI application entrypoint for Market Intelligence (SPEC-004).

``create_app`` is a factory so tests can inject an in-memory database and publisher. The
lifespan handler runs migrations and primes the pipeline's known-symbol set on startup.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from nexus_shared.events.publisher import EventPublisher
from market_intelligence.api.controller import router, ws_router
from market_intelligence.config import Settings, get_settings
from market_intelligence.container import Container

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def create_app(
    settings: Settings | None = None, *, publisher: EventPublisher | None = None
) -> FastAPI:
    settings = settings or get_settings()
    container = Container.build(settings, publisher=publisher)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        await container.startup()
        yield
        await container.shutdown()

    app = FastAPI(
        title="NexusQuant — Market Intelligence Platform",
        version="0.1.0",
        summary="Instrument master, market-data ingestion, data quality, replay (SPEC-004).",
        lifespan=lifespan,
    )
    app.state.container = container
    app.include_router(router)
    app.include_router(ws_router)
    return app


app = create_app()
