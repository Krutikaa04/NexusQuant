
# SPEC-006 — Data Platform & Knowledge Layer
**AegisOS | Version 3.0 | AI Implementation Contract**

## 1. Purpose

Provide the canonical persistence layer for AegisOS. Own all persistent storage,
schema management, data lineage, read models and immutable research artifacts.

---

## 2. Responsibilities

Owns
- PostgreSQL schemas
- Redis cache
- Data lineage
- Dataset versioning
- Feature versioning
- Read models
- Database migrations

Never Owns
- Trading logic
- Strategy logic
- Broker APIs
- AI orchestration

---

## 3. Core Components

- Market Schema
- Research Schema
- Alpha Schema
- Portfolio Schema
- Execution Schema
- Governance Schema
- Redis Cache
- Migration Manager

---

## 4. Schemas

market
- instruments
- ticks
- candles
- corporate_actions
- market_regimes

research
- research_projects
- hypotheses
- experiments
- datasets
- dataset_versions

alpha
- features
- feature_versions
- models
- model_versions

portfolio
- accounts
- portfolios
- positions

execution
- orders
- executions

governance
- approvals
- audit_log

---

## 5. Versioning Rules

Immutable:
- Datasets
- Features
- Models
- Research reports

Append-only history.

---

## 6. API Contracts

GET /data/health
GET /datasets
GET /features
GET /models

---

## 7. Event Contracts

Consumes
- DatasetCreated
- FeatureVersionCreated
- ModelValidated

Publishes
- DatasetIndexed
- ReadModelUpdated

---

## 8. Database Standards

Primary Keys: UUID

Timestamps: UTC

Soft delete:
Only for user-facing metadata.

Research artifacts:
Never deleted.

Indexes:
- timestamp
- version
- project_id
- symbol

---

## 9. Configuration

DB_POOL_SIZE
CACHE_TTL
MIGRATION_TIMEOUT
QUERY_TIMEOUT

---

## 10. Performance

Simple query <50ms

Historical query <250ms

Bulk insert batched

---

## 11. Security

RBAC

Encrypted credentials

Parameterized SQL only

Audit every schema migration

---

## 12. Testing

Unit
- Repositories
- Migrations

Integration
- Transactions
- Cache invalidation

Recovery
- Backup restore

---

## 13. File Structure

services/data_platform/

controllers/
repositories/
migrations/
schemas/
cache/
tests/

---

## 14. Dependency Matrix

Depends On
- SPEC-001
- SPEC-002
- SPEC-003
- SPEC-004
- SPEC-005

Requires
- PostgreSQL
- Redis

Out of Scope
- Portfolio calculations
- Risk rules
- OMS

---

## 15. Claude Implementation Map

Implement in order

1. Migration framework
2. Schemas
3. Repositories
4. Cache
5. APIs
6. Events
7. Tests

Never expose raw SQL outside repositories.

---

## 16. Acceptance Criteria

- Schema versioned
- Immutable datasets
- Repository pattern enforced
- Migrations reproducible
- >90% repository test coverage
