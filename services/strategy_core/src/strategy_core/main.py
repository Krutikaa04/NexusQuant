"""FastAPI application entrypoint for Strategy Core.

``create_app`` is a factory so tests can inject an in-memory database. The lifespan handler
runs migrations on startup.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from strategy_core.api.controller import router
from strategy_core.config import Settings, get_settings
from strategy_core.container import Container

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    container = Container.build(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        await container.startup()
        yield
        await container.shutdown()

    app = FastAPI(
        title="NexusQuant — Strategy Core",
        version="0.1.0",
        summary="Strategy Management & Orchestration: lifecycle, configuration, versioning, health.",
        lifespan=lifespan,
    )
    app.state.container = container
    app.include_router(router)
    return app


app = create_app()
