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
from strategy_core.api.controller import router as strategy_router
from strategy_core.config import Settings as StrategySettings
from strategy_core.container import Container as StrategyContainer

from overview import build_overview
from seed import LiveFeed, seed, use_demo_regime_classifier
from seed_strategies import seed_strategies

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("nexus.backend")

DB_PATH = os.environ.get("NEXUS_DB_PATH", ".dev/market.db")
STRATEGY_DB_PATH = os.environ.get("NEXUS_STRATEGY_DB_PATH", ".dev/strategy.db")
LIVE_FEED = os.environ.get("NEXUS_LIVE_FEED", "1") == "1"

# Trading modules the shell renders. The central entity is the Strategy; every other
# module (portfolio, orders, execution, risk, analytics) operates on strategies and the
# capital allocated to them. Implemented modules link to real pages; the rest render a
# professional "Coming soon" page while their bounded contexts are built.
MODULES = [
    {"key": "market", "name": "Markets", "spec": "SPEC-004", "status": "live",
     "summary": "Validated, normalized market data: instrument master, quality scoring, regimes."},
    {"key": "strategies", "name": "Strategies", "spec": "SPEC-008", "status": "live",
     "summary": "The central entity: entry/exit logic, risk rules, versioning, health and allocation."},
    {"key": "portfolio", "name": "Portfolio", "spec": "SPEC-011", "status": "coming_soon",
     "summary": "Positions, exposure, capital allocation across eligible strategies."},
    {"key": "orders", "name": "Orders", "spec": "SPEC-013", "status": "coming_soon",
     "summary": "Order lifecycle, routing and broker abstraction under governance."},
    {"key": "execution", "name": "Execution", "spec": "SPEC-013", "status": "coming_soon",
     "summary": "Paper and live execution, fills, slippage and reconciliation."},
    {"key": "risk", "name": "Risk", "spec": "SPEC-010", "status": "coming_soon",
     "summary": "Pre-trade limits, drawdown control, strategy pausing and approval gates."},
    {"key": "analytics", "name": "Analytics", "spec": "SPEC-009", "status": "coming_soon",
     "summary": "Backtesting, walk-forward, attribution and strategy performance analytics."},
    {"key": "copilot", "name": "AI Copilot", "spec": "SPEC-012", "status": "coming_soon",
     "summary": "Strategy review, explainability and autonomous-decision narration."},
]

PLATFORM_SERVICES = [
    {"name": "Event Fabric", "spec": "SPEC-005", "status": "implemented",
     "summary": "Versioned event backbone: publish, persist, route, replay."},
    {"name": "Data Platform", "spec": "SPEC-006", "status": "implemented",
     "summary": "Migrations, immutable versioned artifacts, lineage, read models."},
    {"name": "Market Data", "spec": "SPEC-004", "status": "implemented",
     "summary": "Provider abstraction, validation, normalization, quality, calendar, regime, replay."},
    {"name": "Strategy Core", "spec": "SPEC-008", "status": "implemented",
     "summary": "Central entity: lifecycle, versioned configuration, health, audit trail."},
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

    strategy_container = StrategyContainer.build(
        StrategySettings(
            STRATEGY_DATABASE_URL=f"sqlite+aiosqlite:///{STRATEGY_DB_PATH}",
            auth_enabled=False,
            environment="development",
        )
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        await container.startup()
        await seed(container)
        await strategy_container.startup()
        await seed_strategies(strategy_container)
        if LIVE_FEED:
            await live.start()
        yield
        if LIVE_FEED:
            await live.stop()
        await strategy_container.shutdown()
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
    app.state.strategy_container = strategy_container

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
    # The full Strategy Core surface (lifecycle, configuration, versioning, health, audit).
    app.include_router(strategy_router)
    return app


app = create_app()
