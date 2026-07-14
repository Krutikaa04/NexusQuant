
# SPEC-010 — Decision & Risk Intelligence
**AegisOS | Version 3.0 | AI Implementation Contract**

## 1. Purpose

Convert validated strategy outputs into governed investment decisions.
This service is the only authority that can approve a recommendation for
paper or live execution after evaluating portfolio context and risk policies.

---

## 2. Responsibilities

Owns
- Decision Engine
- Confidence Engine
- Risk Policy Engine
- Position Sizing
- Exposure Analysis
- Trade Approval
- Decision Audit

Never Owns
- Strategy generation
- Market ingestion
- Broker execution
- Portfolio persistence

---

## 3. Core Components

- Decision Engine
- Policy Engine
- Position Sizing Engine
- Exposure Analyzer
- Liquidity Checker
- Decision Audit Service

---

## 4. Canonical Types

DecisionRequest
DecisionResult
RiskPolicy
RiskViolation
PositionSize
ExposureSnapshot

---

## 5. Decision Matrix

Inputs
- Strategy Signal
- Confidence Score
- Market Regime
- Portfolio Exposure
- Available Capital
- Liquidity
- Risk Policies

Outputs
- BUY / SELL / HOLD
- Approved / Rejected / Review Required
- Confidence (0-100)
- Position Size
- Reason Codes

---

## 6. Data Model

risk_policies
decision_requests
decision_results
risk_violations
position_sizing_rules

---

## 7. API Contracts

POST /decision/evaluate
GET  /decision/{id}
GET  /risk/policies
PUT  /risk/policies

---

## 8. Event Contracts

Consumes
- AlphaGenerated
- PortfolioUpdated
- MarketRegimeChanged

Publishes
- TradeApproved
- TradeRejected
- RiskViolationDetected
- PositionSizeCalculated

---

## 9. Business Rules

- Every recommendation passes risk evaluation.
- Position size determined before approval.
- Policies are versioned.
- Every rejection includes reason codes.
- Every decision is auditable.

---

## 10. Default Risk Policies

- Max portfolio exposure
- Max position exposure
- Daily loss limit
- Max open positions
- Sector concentration
- Liquidity threshold
- Volatility threshold

---

## 11. Configuration

MAX_DAILY_LOSS
MAX_POSITION_WEIGHT
MAX_SECTOR_WEIGHT
MIN_LIQUIDITY
DEFAULT_RISK_MODEL

---

## 12. Performance

Decision evaluation <10ms
Policy lookup <5ms
Audit write async

---

## 13. Security

RBAC
Immutable decision history
Signed approvals

---

## 14. Testing

Unit
- Policy evaluation
- Position sizing

Integration
- End-to-end decision flow

Regression
- Historical scenarios

---

## 15. File Structure

services/decision/

controllers/
services/
policies/
sizing/
audit/
events/
tests/

---

## 16. Dependency Matrix

Depends On
- SPEC-001..SPEC-009

Requires
- Market Intelligence
- Portfolio Context
- Validation Platform

Out of Scope
- OMS
- Broker APIs

---

## 17. Claude Implementation Sequence

1. Canonical types
2. Policy models
3. Position sizing
4. Decision engine
5. APIs
6. Events
7. Audit
8. Tests

---

## 18. Acceptance Criteria

- No recommendation bypasses risk.
- Reason codes returned for every rejection.
- Policies versioned.
- Decision history immutable.
- >90% core test coverage.
