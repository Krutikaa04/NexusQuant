
# SPEC-005 — Research Event Fabric & Streaming Platform
**AegisOS | Version 3.0 | AI Implementation Contract**

## 1. Purpose

Provide the single communication backbone for AegisOS.

Every bounded context exchanges information only through:
- Versioned Domain Events
- Public REST APIs
- WebSocket Streams

No service may directly write into another service's database.

---

# 2. Responsibilities

Owns
- Event publishing
- Event routing
- WebSocket streaming
- Event replay
- Event versioning
- Event persistence
- Consumer registration

Never Owns
- Business logic
- Portfolio state
- Strategy execution
- Market calculations

---

# 3. Event Categories

## Market
TickReceived
CandleClosed
MarketRegimeChanged
TradingSessionOpened
TradingSessionClosed
CorporateActionApplied

## Research
ResearchProjectCreated
HypothesisCreated
ExperimentStarted
ExperimentCompleted
DatasetCreated
DatasetVersionCreated

## Alpha
FeatureVersionCreated
ModelTrained
ModelValidated
AlphaGenerated

## Decision
RecommendationCreated
ConfidenceUpdated
TradeApproved
TradeRejected

## Execution
OrderSubmitted
OrderFilled
OrderCancelled

## Governance
StrategyPromoted
StrategyRetired
ApprovalGranted
ApprovalRevoked

---

# 4. Standard Event Envelope

Every event contains:

- event_id (UUID)
- event_type
- event_version
- timestamp_utc
- producer
- correlation_id
- payload
- metadata

Events are immutable.

---

# 5. Delivery Guarantees

Internal
- At least once

Consumers
- Idempotent

Ordering
- Per aggregate

Dead Letter Queue
- Invalid schema
- Unknown version
- Processing failure

---

# 6. WebSocket Channels

/ws/market
/ws/research
/ws/portfolio
/ws/orders
/ws/governance
/ws/system

Authentication:
JWT required

---

# 7. REST APIs

GET /events/health
GET /events/metrics
POST /events/replay
GET /events/schema/{event}

---

# 8. Database

Tables

event_store
consumer_offsets
event_schema_versions
dead_letter_events

Indexes

(event_type)
(timestamp_utc)
(correlation_id)

---

# 9. Configuration

EVENT_RETENTION_DAYS
MAX_RETRY_COUNT
WEBSOCKET_HEARTBEAT
REPLAY_BATCH_SIZE

---

# 10. Performance

Publish latency <10ms

WebSocket fanout <100ms

Replay deterministic

---

# 11. Security

JWT authentication

RBAC

Signed internal events

Immutable audit history

---

# 12. Testing

Unit
- Envelope validation
- Schema validation

Integration
- Replay
- Multi-service delivery

Chaos
- Duplicate events
- Consumer crash
- Network partition

---

# 13. File Structure

services/event_fabric/

controllers/
EventController.py

services/
Publisher.py
Subscriber.py
ReplayService.py

schemas/
event.py

events/

tests/

---

# 14. Claude Implementation Map

Implement in order

1. Event schema
2. Publisher
3. Subscriber
4. Replay engine
5. WebSocket gateway
6. REST APIs
7. Tests

Do not implement business logic here.

---

# 15. Acceptance Criteria

- Versioned events
- Deterministic replay
- Zero cross-database writes
- All services communicate through contracts
- 90%+ unit test coverage
