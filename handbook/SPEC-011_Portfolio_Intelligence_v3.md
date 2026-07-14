
# SPEC-011 — Portfolio Intelligence
**AegisOS | Version 3.0 | AI Implementation Contract**

## 1. Purpose

Maintain the canonical investment portfolio, compute portfolio analytics,
measure exposures and provide optimization/rebalancing recommendations for
Decision & Risk Intelligence.

---

## 2. Responsibilities

Owns
- Portfolio state
- Positions
- Cash balances
- PnL calculations
- Exposure analytics
- Portfolio health
- Rebalancing recommendations

Never Owns
- Strategy generation
- Broker execution
- Market ingestion
- Risk approval

---

## 3. Core Components

- Portfolio Manager
- Position Manager
- Analytics Engine
- Exposure Engine
- Rebalancing Engine
- Benchmark Engine

---

## 4. Canonical Types

PortfolioSnapshot
Position
PortfolioAnalytics
ExposureReport
RebalancePlan
PortfolioHealth

---

## 5. Portfolio Metrics

- Total Value
- Cash
- Buying Power
- Unrealized PnL
- Realized PnL
- Daily Return
- CAGR
- Sharpe
- Max Drawdown
- Volatility

---

## 6. Exposure Analytics

Calculate:
- Sector exposure
- Industry exposure
- Instrument exposure
- Market-cap exposure
- Correlation matrix
- Diversification score
- Capital utilization

---

## 7. Data Model

accounts
portfolios
positions
portfolio_snapshots
portfolio_analytics
benchmarks

---

## 8. API Contracts

GET  /portfolio
GET  /portfolio/positions
GET  /portfolio/analytics
GET  /portfolio/exposure
POST /portfolio/rebalance

---

## 9. Event Contracts

Consumes
- OrderFilled
- TradeApproved
- MarketRegimeChanged

Publishes
- PortfolioUpdated
- PositionUpdated
- RebalanceSuggested
- PortfolioHealthUpdated

---

## 10. Business Rules

- Portfolio is the single source of truth.
- Every fill updates positions.
- Analytics use immutable snapshots.
- Rebalancing never executes trades directly.
- Benchmark comparison is configurable.

---

## 11. Configuration

BASE_CURRENCY
DEFAULT_BENCHMARK
REBALANCE_THRESHOLD
SNAPSHOT_INTERVAL

---

## 12. Performance

Portfolio update <20ms
Analytics refresh <100ms
Snapshot creation async

---

## 13. Security

RBAC
Immutable historical snapshots
Audit portfolio changes

---

## 14. Testing

Unit
- PnL
- Exposure
- Rebalancing

Integration
- Order-to-portfolio flow

Regression
- Historical portfolio replay

---

## 15. File Structure

services/portfolio/

controllers/
services/
analytics/
rebalancing/
repositories/
events/
tests/

---

## 16. Dependency Matrix

Depends On
- SPEC-001..SPEC-010

Requires
- Data Platform
- Event Fabric
- Decision Engine

Out of Scope
- OMS
- Strategy SDK

---

## 17. Claude Implementation Sequence

1. Canonical types
2. Portfolio models
3. Analytics engine
4. Exposure engine
5. Rebalancing engine
6. APIs
7. Events
8. Tests

---

## 18. Acceptance Criteria

- Portfolio is authoritative.
- Exposure metrics available.
- Rebalance plans reproducible.
- Immutable snapshots maintained.
- >90% core test coverage.
