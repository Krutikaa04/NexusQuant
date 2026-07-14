"""FastAPI application entrypoint for the Event Fabric (SPEC-005).

``create_app`` is a factory so tests can build an isolated instance with an in-memory
database and a private schema registry. The lifespan handler owns the container's startup
(create tables) and shutdown (dispose engine).
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from nexus_shared.events.registry import SchemaRegistry
from event_fabric.api.controller import router, ws_router
from event_fabric.config import Settings, get_settings
from event_fabric.container import Container

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def create_app(
    settings: Settings | None = None, *, registry: SchemaRegistry | None = None
) -> FastAPI:
    settings = settings or get_settings()
    container = Container.build(settings, registry=registry)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        await container.startup()
        yield
        await container.shutdown()

    app = FastAPI(
        title="NexusQuant — Research Event Fabric",
        version="0.1.0",
        summary="Versioned event backbone (SPEC-005).",
        lifespan=lifespan,
    )
    app.state.container = container
    app.include_router(router)
    app.include_router(ws_router)
    return app


app = create_app()
