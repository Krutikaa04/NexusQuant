# NexusQuant

**Institutional Quantitative Research & Execution Platform for the Indian Equity Market.**

NexusQuant is not an algorithmic trading bot. It is a governed research platform where
**research is the product** and every production trade originates from a validated research
workflow. See [`handbook/`](handbook/) for the authoritative engineering specifications
(SPEC-001 … SPEC-015).

## Architecture

An event-driven monorepo of independently-deployable **bounded contexts** (SPEC-002 / SPEC-003).
Contexts communicate *only* through versioned domain events, public REST APIs, and WebSocket
streams — never through shared database writes.

```
Market Intelligence → Research OS → Alpha Factory → Decision Intelligence
   → Portfolio & Risk → Execution → Governance & Observability
```

### Repository layout

```
handbook/                 Authoritative specifications (source of truth)
packages/
  nexus-shared/           Domain kernel: event envelope, catalog, primitives (contracts only)
  nexus-platform/         Technical kernel: async DB session, base repository, cache, migration runner
services/
  event_fabric/           SPEC-005 — Research Event Fabric (communication backbone)
  data_platform/          SPEC-006 — Data Platform (migrations, immutable artifacts, lineage, read models)
  market_intelligence/    SPEC-004 — Market Intelligence (instruments, ingestion, quality, calendar, regime)
  ...                     One directory per bounded context (added incrementally)
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
            -e services/event_fabric -e services/data_platform -e services/market_intelligence

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

| Layer | Spec | Status |
|-------|------|--------|
| Research Event Fabric   | SPEC-005 | 🟢 Implemented (tested) |
| Data Platform           | SPEC-006 | 🟢 Implemented (tested) |
| Market Intelligence     | SPEC-004 | 🟢 Implemented (tested) |
| Research OS             | SPEC-007 | ⚪ Planned |
| Alpha Factory           | SPEC-008 | ⚪ Planned |
| Validation Platform     | SPEC-009 | ⚪ Planned |
| Decision & Risk         | SPEC-010 | ⚪ Planned |
| Portfolio Intelligence  | SPEC-011 | ⚪ Planned |
| AI Quant Copilot        | SPEC-012 | ⚪ Planned |
| Execution & OMS         | SPEC-013 | ⚪ Planned |
| ML & Alpha Discovery    | SPEC-014 | ⚪ Planned |
| Governance & Observability | SPEC-015 | ⚪ Planned |
