
# SPEC-007 — Research Operating System
**AegisOS | Version 3.0 | AI Implementation Contract**

## 1. Purpose

The Research Operating System (Research OS) is the central workspace for all
quantitative research. Every strategy begins as a research project and moves
through a governed lifecycle before it can reach paper or live trading.

---

## 2. Responsibilities

Owns
- Research projects
- Hypotheses
- Experiments
- Research notebooks
- Dataset lineage
- Feature lineage
- Research reviews
- Strategy promotion workflow

Never Owns
- Live order execution
- Portfolio accounting
- Market data ingestion
- Broker communication

---

## 3. Core Components

- Project Manager
- Hypothesis Manager
- Experiment Manager
- Notebook Service
- Dataset Registry
- Research Review Engine
- Promotion Pipeline
- Research Dashboard

---

## 4. Research Lifecycle

Draft
→ Active
→ Experimenting
→ Validated
→ Paper Trading
→ Production Candidate
→ Approved
→ Retired

State changes require review events.

---

## 5. Data Model

research_projects
- id
- name
- owner
- status
- created_at

hypotheses
- id
- project_id
- statement
- success_criteria

experiments
- id
- project_id
- dataset_version
- feature_version
- status
- metrics

research_reviews
- id
- project_id
- reviewer
- decision
- comments

---

## 6. API Contracts

POST /research/projects
GET  /research/projects
GET  /research/projects/{id}

POST /research/hypotheses
POST /research/experiments
POST /research/reviews

---

## 7. Event Contracts

Publishes
- ResearchProjectCreated
- HypothesisCreated
- ExperimentStarted
- ExperimentCompleted
- ResearchReviewed
- StrategyPromoted

Consumes
- DatasetCreated
- FeatureVersionCreated
- ModelValidated

---

## 8. Business Rules

- Every experiment belongs to one project.
- Projects require at least one hypothesis.
- Production promotion requires successful review.
- Research artifacts are immutable after approval.
- All experiments reference explicit dataset and feature versions.

---

## 9. Configuration

MAX_PROJECTS_PER_USER
AUTO_ARCHIVE_DAYS
REVIEW_REQUIRED=true
DEFAULT_EXPERIMENT_TIMEOUT

---

## 10. Performance

Project lookup <50ms
Experiment creation <100ms
Dashboard refresh <250ms

---

## 11. Security

JWT authentication
RBAC
Project-level authorization
Immutable audit trail

---

## 12. Testing

Unit
- Lifecycle transitions
- Review rules
- Promotion rules

Integration
- Experiment workflow
- Event publication

Regression
- Reproducible experiment history

---

## 13. File Structure

services/research_os/

controllers/
ProjectController.py
ExperimentController.py

services/
ProjectService.py
ExperimentService.py
ReviewService.py

repositories/
schemas/
events/
tests/

---

## 14. Dependency Matrix

Depends On
- SPEC-001
- SPEC-002
- SPEC-003
- SPEC-004
- SPEC-005
- SPEC-006

Requires
- Event Fabric
- Data Platform

Out of Scope
- Alpha generation
- Risk evaluation
- OMS

---

## 15. Claude Implementation Sequence

1. Database models
2. Domain entities
3. Repositories
4. Services
5. Lifecycle state machine
6. REST APIs
7. Domain events
8. Tests
9. Documentation

---

## 16. Acceptance Criteria

- Research lifecycle enforced
- Immutable approved artifacts
- Version-aware experiments
- Event-driven promotion
- >90% service test coverage
