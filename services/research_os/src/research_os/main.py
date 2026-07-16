"""FastAPI application entrypoint for the Research OS (SPEC-007)."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from nexus_shared.events.publisher import EventPublisher
from research_os.api.controller import router
from research_os.config import Settings, get_settings
from research_os.container import Container

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
        title="NexusQuant — Research Operating System",
        version="0.1.0",
        summary="Governed research lifecycle: projects, hypotheses, experiments, reviews (SPEC-007).",
        lifespan=lifespan,
    )
    app.state.research_container = container
    app.include_router(router)
    return app


app = create_app()
