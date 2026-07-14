
# SPEC-003 — Domain-Driven Design & Bounded Contexts
## AegisOS
### Version 2.0 (Institutional Edition)

## Executive Summary

This specification defines the business domains, ownership boundaries, ubiquitous
language, integration rules, and domain contracts for AegisOS. Every capability
belongs to exactly one bounded context. Cross-context communication occurs only
through documented APIs or versioned domain events.

---

# Core Principles

- Single ownership for every business capability.
- Event-first integration.
- Immutable market facts.
- Version everything.
- No shared database writes.
- Research artifacts are first-class citizens.

---

# Ubiquitous Language

| Term | Definition | Owner |
|---|---|---|
| Research Project | Parent container for all research | Research OS |
| Hypothesis | Research question to validate | Research OS |
| Experiment | Controlled evaluation | Research OS |
| Dataset | Immutable research dataset | Data Platform |
| Feature | Engineered market variable | Alpha Factory |
| Model | Predictive artifact | Alpha Factory |
| Recommendation | Risk-aware investment proposal | Decision Intelligence |
| Approval | Governance decision | Governance |
| Position | Live portfolio exposure | Portfolio Intelligence |

---

# Bounded Contexts

## 1. Market Intelligence

Owns:
- Instrument master
- Tick ingestion
- Candles
- Trading sessions
- Corporate actions
- Trading calendar
- Market regime detection
- Data quality score

Publishes:
- TickReceived
- CandleClosed
- MarketRegimeChanged
- DataQualityChanged

Never owns:
- Strategies
- Risk
- Orders

---

## 2. Research Operating System

Owns:
- Projects
- Hypotheses
- Experiments
- Research notebooks
- Reviews
- Dataset lineage
- Feature lineage

Lifecycle:

Idea → Hypothesis → Experiment → Review → Approved Research

---

## 3. Alpha Factory

Owns:
- Indicator engine
- Feature engineering
- Feature Store
- ML training
- Optimization
- Alpha generation

Outputs:
- AlphaSignal
- FeatureVersion
- ModelVersion

---

## 4. Decision Intelligence

Owns:
- Ensemble engine
- Confidence engine
- Recommendation engine
- Strategy ranking

Produces:
- InvestmentRecommendation

Consumes:
- Alpha signals
- Portfolio state
- Risk context
- Market regime

---

## 5. Portfolio & Risk Intelligence

Owns:
- Portfolio state
- Positions
- Allocation
- Exposure
- Position sizing
- Risk policies

Produces:
- TradeApproved
- TradeRejected
- RebalanceSuggested

---

## 6. Execution Intelligence

Owns:
- OMS
- Broker adapters
- Paper trading
- Live trading
- Execution analytics
- Reconciliation

Produces:
- OrderFilled
- ExecutionQualityUpdated

---

## 7. AI Quant Copilot

Owns:
- Research assistance
- Report generation
- Strategy reviews
- Explainability
- Documentation

Never owns business rules.

---

## 8. Governance & Observability

Owns:
- Audit logs
- Strategy promotion
- Model approval
- Dataset approval
- Monitoring
- Metrics
- Traceability

---

# Context Map

Market Intelligence
    ↓
Research OS
    ↓
Alpha Factory
    ↓
Decision Intelligence
    ↓
Portfolio & Risk
    ↓
Execution Intelligence
    ↓
Governance

AI Quant Copilot interacts with every domain through APIs only.

---

# Domain Events

Research:
- HypothesisCreated
- ExperimentStarted
- ExperimentCompleted
- ResearchReviewed

Alpha:
- FeatureVersionCreated
- ModelValidated
- AlphaGenerated

Decision:
- RecommendationCreated
- ConfidenceUpdated

Governance:
- StrategyPromoted
- StrategyRetired
- ApprovalGranted
- ApprovalRevoked

---

# Ownership Rules

- Every aggregate has one owner.
- Cross-domain writes are forbidden.
- Reads occur via APIs, events, or read models.
- Event schemas require semantic versioning.

---

# Aggregate Roots

- Instrument
- ResearchProject
- Dataset
- Experiment
- FeatureSet
- Model
- Recommendation
- Portfolio
- Order
- AuditRecord

---

# Acceptance Criteria

- Every business capability assigned to one context.
- No duplicated ownership.
- Event contracts documented.
- APIs respect boundaries.
- Governance covers every production artifact.

---

# Claude Code Contract

Claude Code shall:
- Preserve bounded-context isolation.
- Avoid leaking business logic across services.
- Use shared packages only for contracts and primitives.
- Never bypass Governance & Observability.
