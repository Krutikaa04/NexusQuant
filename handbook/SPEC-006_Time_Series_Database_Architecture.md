
# SPEC-006 — Time-Series Database & Storage Architecture
Version: 1.0

## Executive Summary
This specification defines the persistence layer for QuantForge AI. It establishes
how market data, research artifacts, strategies, portfolios, orders and AI outputs
are stored, queried, partitioned, archived and backed up.

---

# 1. Design Goals

- Immutable market history
- Fast time-range queries
- Horizontal growth
- Deterministic replay
- Clear ownership per bounded context

---

# 2. Database Topology

Primary datastore:
- PostgreSQL

Cache:
- Redis

Storage groups:
- market
- research
- strategy
- portfolio
- risk
- execution
- ai
- audit

---

# 3. Schema Overview

## market
Tables:
- instruments
- trading_sessions
- ticks
- candles_1s
- candles_1m
- candles_5m
- candles_15m
- candles_1h
- candles_1d

## research
- indicators
- engineered_features
- experiments
- feature_store

## strategy
- strategies
- strategy_versions
- signals
- optimization_jobs

## portfolio
- accounts
- portfolios
- positions
- pnl_snapshots

## execution
- orders
- executions
- broker_events

## risk
- policies
- approvals
- violations

## ai
- conversations
- reports
- generated_strategies

## audit
- event_log
- configuration_changes

---

# 4. Partitioning Strategy

Ticks:
Partition by month and symbol.

Candles:
Partition by timeframe and month.

Audit:
Append-only monthly partitions.

---

# 5. Indexing

Ticks:
(symbol, timestamp)

Candles:
(symbol, interval, open_time)

Signals:
(strategy_id, created_at)

Orders:
(account_id, created_at)

---

# 6. Read / Write Rules

Writes:
Only owning service may write.

Reads:
Other services use APIs or read replicas.

Direct cross-context writes are prohibited.

---

# 7. Repository Pattern

Each service exposes:

- Repository Interface
- Query Service
- Transaction Manager
- Migration Module

Business logic never resides in SQL migrations.

---

# 8. Backup Strategy

Daily logical backup

Weekly full snapshot

Monthly archive

Restore tests executed every release cycle.

---

# 9. Retention

Ticks:
Archive after configurable retention period.

Candles:
Permanent.

Orders:
Permanent.

Audit:
Permanent.

---

# 10. Performance Targets

Tick insert:
<20 ms

Historical candle query:
<250 ms

Portfolio lookup:
<100 ms

---

# 11. Migration Rules

- Forward-only migrations
- Version controlled
- Repeatable seed data
- Rollback plan documented

---

# 12. Testing

Unit:
Repository behavior

Integration:
Transaction boundaries

Load:
Bulk ingest
Concurrent readers

Recovery:
Backup restore validation

---

# 13. Acceptance Criteria

- Schema documented
- Migrations reproducible
- Required indexes created
- Cross-context ownership enforced
- Backup procedure validated

---

# 14. Claude Code Guidance

Implement migrations before repositories.
Never expose raw SQL outside persistence layer.
Preserve backward compatibility for schema changes using explicit migration versions.
