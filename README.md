# NexusQuant

**Institutional-grade Autonomous Algorithmic Trading Operating System for the Indian Equity Market.**

NexusQuant is a production-oriented autonomous trading platform. The **Strategy is the central
entity** — the platform autonomously determines which strategies are eligible, which market regime
is active, which strategies receive capital, which are paused, and when a strategy should be
retired or requires human approval. Every order is governed, explainable, and reproducible.
See [`handbook/`](handbook/) for the authoritative engineering specifications (SPEC-001 … SPEC-015).

## Architecture

An event-driven monorepo of independently-deployable **bounded contexts** (SPEC-002 / SPEC-003).
Contexts communicate *only* through versioned domain events, public REST APIs, and WebSocket
streams — never through shared database writes.

```
Market Data → Strategy Core → Portfolio → Risk → Orders → Execution
   → Analytics · AI Copilot · Governance & Observability (cross-cutting)
```

### Repository layout

```
handbook/                 Authoritative specifications (source of truth)
packages/
  nexus-shared/           Domain kernel: event envelope, catalog, primitives (contracts only)
  nexus-platform/         Technical kernel: async DB session, base repository, cache, migration runner
services/
  event_fabric/           SPEC-005 — Event Fabric (communication backbone)
  data_platform/          SPEC-006 — Data Platform (migrations, immutable artifacts, lineage, read models)
  market_intelligence/    SPEC-004 — Market Data (provider abstraction, ingestion, validation, quality, regime)
  strategy_core/          SPEC-008 — Strategy Core (central entity: lifecycle, versioned config, health, audit)
  ...                     Downstream trading contexts (portfolio, orders, execution, risk — added incrementally)
frontend/                 Next.js presentation layer (added later)
infra/
  docker-compose.yml      Local Postgres + Redis
```

The shared kernel holds **contracts and primitives only** — never business logic (SPEC-003).

## Tech stack

| Concern        | Choice                                    |
|----------------|-------------------------------------------|
| Services       | Python 3.11+, FastAPI, Pydantic v2        |
| Persistence    | PostgreSQL (async SQLAlchemy 2.0)         |
| Cache / pubsub | Redis                                     |
| Presentation   | Next.js (TypeScript)                       |
| Packaging      | Per-service `pyproject.toml`, editable shared kernel |
| Tests          | pytest + in-memory SQLite / fakeredis (no external services required) |

## Run the app (single command)

A dev launcher starts the Python backend **and** the Next.js frontend together, seeds a
demo NSE universe through the real SPEC-004 pipeline, and runs a gentle live feed:

```bash
# one-time: create the venv and install the Python packages (editable)
python -m venv .venv && . .venv/Scripts/activate      # POSIX: source .venv/bin/activate
pip install -e packages/nexus-shared -e packages/nexus-platform \
            -e services/event_fabric -e services/data_platform \
            -e services/market_intelligence -e services/strategy_core

# then, every time:
python run.py
```

- **App**  → http://localhost:3000  (landing, dashboard, live Market Intelligence)
- **API**  → http://localhost:8004  (OpenAPI docs at `/docs`)

`run.py` installs the frontend's npm dependencies on first run. Requires Python 3.11+ and
Node 18+. The frontend proxies `/api` and `/market` to the backend, so no CORS config is
needed. The dashboard and charts poll live; the backend live feed updates prices every ~1.5s.

## Working on a single service

```bash
docker compose -f infra/docker-compose.yml up -d          # optional: real Postgres + Redis
uvicorn market_intelligence.main:app --reload --port 8004  # a bare service
pytest                                                     # full suite, no infra required
```

## Implementation status

| Module | Spec | Status |
|-------|------|--------|
| Event Fabric            | SPEC-005 | 🟢 Implemented (tested) |
| Data Platform           | SPEC-006 | 🟢 Implemented (tested) |
| Market Data             | SPEC-004 | 🟢 Implemented (tested) |
| Strategy Core           | SPEC-008 | 🟢 Implemented (tested, central entity) |
| Portfolio               | SPEC-011 | ⚪ Planned |
| Orders                  | SPEC-013 | ⚪ Planned |
| Execution               | SPEC-013 | ⚪ Planned |
| Risk                    | SPEC-010 | ⚪ Planned |
| Analytics               | SPEC-009 | ⚪ Planned |
| AI Copilot              | SPEC-012 | ⚪ Planned |
| Governance & Observability | SPEC-015 | ⚪ Planned |
