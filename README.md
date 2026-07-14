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

## Development

```bash
# 1. Start infrastructure (Postgres + Redis)
docker compose -f infra/docker-compose.yml up -d

# 2. Install a service and the shared kernel (editable)
cd services/event_fabric
pip install -e ../../packages/nexus-shared -e .[dev]

# 3. Run the service
uvicorn event_fabric.main:app --reload --port 8005

# 4. Tests (require no running infrastructure)
pytest
```

## Implementation status

| Layer | Spec | Status |
|-------|------|--------|
| Research Event Fabric   | SPEC-005 | 🟢 Implemented (tested) |
| Data Platform           | SPEC-006 | 🟢 Implemented (tested) |
| Market Intelligence     | SPEC-004 | ⚪ Next |
| Research OS             | SPEC-007 | ⚪ Planned |
| Alpha Factory           | SPEC-008 | ⚪ Planned |
| Validation Platform     | SPEC-009 | ⚪ Planned |
| Decision & Risk         | SPEC-010 | ⚪ Planned |
| Portfolio Intelligence  | SPEC-011 | ⚪ Planned |
| AI Quant Copilot        | SPEC-012 | ⚪ Planned |
| Execution & OMS         | SPEC-013 | ⚪ Planned |
| ML & Alpha Discovery    | SPEC-014 | ⚪ Planned |
| Governance & Observability | SPEC-015 | ⚪ Planned |
