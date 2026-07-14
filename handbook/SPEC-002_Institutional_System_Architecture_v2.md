
# SPEC-002 — Institutional System Architecture
## AegisOS
### Version 2.0 (Vision Locked)

# Executive Summary

This document defines the macro-architecture of AegisOS. The platform is organized
around institutional responsibilities instead of technical services. Research is
the central workflow, while execution is a governed downstream capability.

---

# Architectural Principles

1. Research First
2. Event-Driven Communication
3. Domain-Driven Design
4. Immutable Market Data
5. Deterministic Computation
6. Explainable Decisions
7. Zero Trust Between Services
8. Governance by Default

---

# Eight Layer Architecture

## Layer 1 – Market Intelligence
Responsibilities:
- Live NSE market ingestion
- Historical data
- Trading calendar
- Corporate actions
- Market regime detection
- Data quality engine
- Instrument master

Publishes:
- TickReceived
- CandleClosed
- MarketRegimeUpdated
- DataQualityChanged

---

## Layer 2 – Research Operating System
Responsibilities:
- Research projects
- Hypotheses
- Experiments
- Research notebooks
- Dataset lineage
- Feature lineage
- Experiment registry

---

## Layer 3 – Alpha Factory
Responsibilities:
- Feature engineering
- Indicator engine
- Alpha generation
- ML pipelines
- Feature Store
- Optimization

---

## Layer 4 – Decision Intelligence
Responsibilities:
- Strategy ensemble
- Confidence scoring
- Recommendation engine
- Strategy ranking
- Promotion readiness

Decision pipeline:
Signal → Confidence → Portfolio Context → Risk → Recommendation

---

## Layer 5 – Portfolio & Risk Intelligence
Responsibilities:
- Portfolio state
- Position sizing
- Exposure
- Correlation
- Drawdown
- Capital allocation
- Risk policy enforcement

---

## Layer 6 – Execution Intelligence
Responsibilities:
- OMS
- Broker adapters
- Execution analytics
- Paper trading
- Live execution
- Reconciliation

---

## Layer 7 – AI Quant Copilot
Responsibilities:
- Research assistant
- Code review
- Strategy review
- Explainability
- Daily reports
- Documentation generation

Uses documented APIs only.

---

## Layer 8 – Governance & Observability
Responsibilities:
- Audit logs
- Strategy lifecycle
- Dataset versioning
- Model governance
- Monitoring
- Metrics
- Tracing

---

# End-to-End Workflow

Idea
→ Research Project
→ Dataset
→ Feature Engineering
→ Alpha Discovery
→ Validation
→ Paper Trading
→ Decision Intelligence
→ Risk Approval
→ Execution
→ Monitoring
→ Retirement

---

# Service Boundaries

Every domain exposes:
- REST API
- Event interface
- Health endpoint
- Metrics endpoint

No service may directly modify another service's database.

---

# Deployment Model

Presentation:
- Next.js

Application:
- FastAPI domain services

Persistence:
- PostgreSQL
- Redis

Infrastructure:
- Docker
- GitHub Actions
- Free-tier cloud for development

---

# Architecture Decision Records

ADR-001:
Research is the primary product.

ADR-002:
Trading requires research validation.

ADR-003:
All communication is event-first.

ADR-004:
Market data is immutable.

ADR-005:
Every production artifact is versioned.

---

# Non-Functional Requirements

Latency:
Dashboard updates <100 ms.

Availability:
Automatic recovery from feed interruptions.

Security:
JWT, RBAC, encrypted secrets.

Observability:
Structured logs, metrics, distributed traces.

---

# Acceptance Criteria

- Clear ownership for every domain.
- No cyclic dependencies.
- APIs documented.
- Events versioned.
- Service contracts tested.
- Architecture diagrams updated before implementation.

---

# Claude Code Contract

Claude Code shall:
- Respect service boundaries.
- Never bypass governance.
- Never introduce undocumented APIs.
- Implement one bounded context at a time.
- Keep every architectural decision consistent with SPEC-001.
