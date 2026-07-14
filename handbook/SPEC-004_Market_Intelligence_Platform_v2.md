
# SPEC-004 — Market Intelligence Platform
## AegisOS
### Version 2.0 (Institutional Edition)

## Executive Summary

The Market Intelligence Platform is the foundation of AegisOS. Unlike a traditional
market data service, it is responsible for transforming raw exchange feeds into
trusted, research-grade market intelligence.

Every downstream component depends on this layer. If market intelligence is
incorrect or incomplete, research, risk, portfolio analytics, and execution are
all compromised.

---

# Vision

Provide a canonical, immutable, and high-confidence representation of the Indian
equity market suitable for institutional quantitative research.

---

# Responsibilities

Owns:

- Live market data ingestion
- Historical time-series storage
- Instrument Master
- Trading calendars
- Corporate actions
- Symbol lifecycle management
- Index constituents
- Sector classifications
- Market regime detection
- Data quality scoring
- Trading readiness assessment
- Replay engine
- Vendor abstraction

Never owns:

- Trading strategies
- Risk policies
- Portfolio state
- Order execution

---

# Core Architecture

Exchange Feed
    ↓
Vendor Adapter
    ↓
Collector
    ↓
Validator
    ↓
Normalizer
    ↓
Data Quality Engine
    ↓
Market Intelligence Store
    ↓
Event Publisher
    ↓
Research Operating System

---

# Subsystems

## Instrument Master

Maintains canonical metadata.

Fields include:
- NSE/BSE symbol
- ISIN
- Tick size
- Lot size
- Sector
- Industry
- Expiry
- Strike
- Option type
- Currency
- Listing status

---

## Trading Calendar

Tracks:

- Trading holidays
- Muhurat trading
- Special sessions
- Pre-open
- Auction windows
- Expiry dates
- Weekly expiry
- Monthly expiry

Publishes:
TradingSessionOpened
TradingSessionClosed

---

## Corporate Actions Engine

Tracks:

- Dividends
- Splits
- Bonus issues
- Rights issues
- Mergers
- Demergers
- Symbol changes

Historical datasets remain reproducible by versioning adjustments.

---

## Market Regime Engine

Continuously classifies the market.

Supported regimes:

- Bull
- Bear
- Sideways
- High Volatility
- Low Volatility
- Earnings Season
- Budget Week
- Election Cycle
- Expiry Week

Outputs:
MarketRegimeChanged

---

## Data Quality Engine

Every market event receives a quality score.

Metrics:

- Feed latency
- Duplicate rate
- Missing packets
- Timestamp drift
- Sequence gaps
- Symbol validation

Produces:

Quality Score
Confidence Level
Trading Readiness

If readiness falls below threshold:

- Suspend paper trading (configurable)
- Block live execution (configurable)
- Raise alerts

---

## Replay Engine

Supports:

- Tick replay
- Candle replay
- Accelerated replay
- Step debugging

Replay must reproduce identical downstream events.

---

# Domain Events

Publishes:

- TickReceived
- CandleClosed
- InstrumentUpdated
- CorporateActionApplied
- MarketRegimeChanged
- TradingSessionOpened
- TradingSessionClosed
- DataQualityChanged

---

# Public APIs

GET /market/instruments
GET /market/candles
GET /market/ticks
GET /market/calendar
GET /market/corporate-actions
GET /market/regime
GET /market/quality

WebSockets

/ws/market
/ws/regime
/ws/calendar

---

# Performance Targets

Tick validation:
<5 ms

Tick persistence:
<20 ms

Regime refresh:
<1 s

Dashboard propagation:
<100 ms

---

# Reliability

- Automatic reconnect
- Exponential backoff
- Vendor failover abstraction
- Duplicate suppression
- Immutable persistence
- Continuous health monitoring

---

# Security

- Authenticated APIs
- Signed internal events
- Audit logging
- Immutable historical records

---

# Testing Strategy

Unit:
- Tick validation
- Candle aggregation
- Calendar rules
- Corporate action processing
- Regime classification

Integration:
- Feed replay
- Event propagation
- Recovery testing

Chaos:
- Feed interruption
- Out-of-order packets
- Clock skew
- Duplicate events

---

# Acceptance Criteria

- Market data is immutable.
- Instrument master is versioned.
- Corporate actions preserve historical reproducibility.
- Data quality is continuously measured.
- Market regime is available as a platform service.
- Replay produces deterministic outputs.

---

# Claude Code Contract

Implement this specification before every other domain service.

No downstream service may ingest exchange feeds directly.

All services must consume market intelligence through documented APIs or
versioned domain events.
