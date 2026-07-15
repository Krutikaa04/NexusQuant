"""NexusQuant development backend (backend-for-frontend).

Composes the real SPEC-004 Market Intelligence service, adds CORS for the Next.js dev
server, seeds a demo universe, runs a gentle live feed, and exposes a couple of aggregation
endpoints for the dashboard. This is a *thin composition* over the shipped service — it adds
no market business logic and does not modify SPEC-004.

Run:  uvicorn main:app --app-dir apps/backend --port 8004 --reload
"""

from __future__ import annotations

import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from market_intelligence.api.controller import router as market_router
from market_intelligence.api.controller import ws_router
from market_intelligence.config import Settings
from market_intelligence.container import Container

from overview import build_overview
from seed import LiveFeed, seed, use_demo_regime_classifier

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("nexus.backend")

DB_PATH = os.environ.get("NEXUS_DB_PATH", ".dev/market.db")
LIVE_FEED = os.environ.get("NEXUS_LIVE_FEED", "1") == "1"

# Modules the shell renders. Implemented ones link to real pages; the rest render a
# professional "Coming soon" page. Kept in sync with the handbook dev-order.
MODULES = [
    {"key": "market", "name": "Market Intelligence", "spec": "SPEC-004", "status": "live",
     "summary": "Canonical market data, instrument master, data-quality scoring, regimes."},
    {"key": "research", "name": "Research OS", "spec": "SPEC-007", "status": "coming_soon",
     "summary": "Governed research lifecycle: projects, hypotheses, experiments, reviews."},
    {"key": "alpha", "name": "Alpha Factory", "spec": "SPEC-008", "status": "coming_soon",
     "summary": "Feature engineering, indicators, alpha generation and the feature store."},
    {"key": "validation", "name": "Validation Platform", "spec": "SPEC-009", "status": "coming_soon",
     "summary": "Backtesting, walk-forward and Monte-Carlo statistical validation."},
    {"key": "decision", "name": "Decision Engine", "spec": "SPEC-010", "status": "coming_soon",
     "summary": "Confidence scoring, ensemble voting and risk-aware recommendations."},
    {"key": "portfolio", "name": "Portfolio Intelligence", "spec": "SPEC-011", "status": "coming_soon",
     "summary": "Portfolio construction, exposure, position sizing and risk controls."},
    {"key": "execution", "name": "Execution & OMS", "spec": "SPEC-013", "status": "coming_soon",
     "summary": "Order management, broker abstraction, paper and live execution analytics."},
    {"key": "copilot", "name": "AI Quant Copilot", "spec": "SPEC-012", "status": "coming_soon",
     "summary": "Research assistant, strategy review, explainability and report generation."},
]

PLATFORM_SERVICES = [
    {"name": "Research Event Fabric", "spec": "SPEC-005", "status": "implemented",
     "summary": "Versioned event backbone: publish, persist, route, replay."},
    {"name": "Data Platform", "spec": "SPEC-006", "status": "implemented",
     "summary": "Migrations, immutable versioned artifacts, lineage, read models."},
    {"name": "Market Intelligence", "spec": "SPEC-004", "status": "implemented",
     "summary": "Instrument master, ingestion pipeline, quality, calendar, regime, replay."},
]


def create_app() -> FastAPI:
    settings = Settings(
        MARKET_DATABASE_URL=f"sqlite+aiosqlite:///{DB_PATH}",
        auth_enabled=False,
        environment="development",
    )
    container = Container.build(settings)
    use_demo_regime_classifier(container)
    live = LiveFeed(container)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        await container.startup()
        await seed(container)
        if LIVE_FEED:
            await live.start()
        yield
        if LIVE_FEED:
            await live.stop()
        await container.shutdown()

    app = FastAPI(
        title="NexusQuant — Development Backend",
        version="0.1.0",
        summary="Backend-for-frontend composing the Market Intelligence service.",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # dev only
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.state.container = container

    @app.get("/api/health", tags=["backend"])
    async def health() -> dict:
        return {"status": "ok", "service": "nexus-backend", "live_feed": LIVE_FEED}

    @app.get("/api/system", tags=["backend"])
    async def system() -> dict:
        return {"modules": MODULES, "services": PLATFORM_SERVICES}

    @app.get("/api/overview", tags=["backend"])
    async def overview(request: Request) -> dict:
        return await build_overview(request.app.state.container)

    # The full SPEC-004 surface (instruments, ticks, candles, quality, calendar,
    # corporate actions, regime, replay) and the /ws/{channel} streams.
    app.include_router(market_router)
    app.include_router(ws_router)
    return app


app = create_app()
