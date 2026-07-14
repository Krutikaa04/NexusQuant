"""The canonical catalog of domain event types (SPEC-005 §3).

This is the single authoritative enumeration of every event that may cross a bounded
context. Producers and consumers reference these members rather than raw strings so
that typos and undocumented events are impossible. Each member's value is the wire
``event_type`` string carried in the envelope.

Adding an event here is a deliberate contract change and must accompany a spec update.
"""

from __future__ import annotations

from enum import Enum


class EventCategory(str, Enum):
    """Top-level grouping used for routing and WebSocket channel selection."""

    MARKET = "market"
    RESEARCH = "research"
    ALPHA = "alpha"
    DECISION = "decision"
    PORTFOLIO = "portfolio"
    EXECUTION = "execution"
    GOVERNANCE = "governance"
    SYSTEM = "system"


class EventType(str, Enum):
    """Every versioned domain event recognised by the platform (SPEC-005 §3)."""

    # --- Market (SPEC-004) ---
    TICK_RECEIVED = "market.TickReceived"
    CANDLE_CLOSED = "market.CandleClosed"
    MARKET_REGIME_CHANGED = "market.MarketRegimeChanged"
    TRADING_SESSION_OPENED = "market.TradingSessionOpened"
    TRADING_SESSION_CLOSED = "market.TradingSessionClosed"
    CORPORATE_ACTION_APPLIED = "market.CorporateActionApplied"
    INSTRUMENT_UPDATED = "market.InstrumentUpdated"
    DATA_QUALITY_CHANGED = "market.DataQualityChanged"

    # --- Research (SPEC-007) ---
    RESEARCH_PROJECT_CREATED = "research.ResearchProjectCreated"
    HYPOTHESIS_CREATED = "research.HypothesisCreated"
    EXPERIMENT_STARTED = "research.ExperimentStarted"
    EXPERIMENT_COMPLETED = "research.ExperimentCompleted"
    RESEARCH_REVIEWED = "research.ResearchReviewed"
    DATASET_CREATED = "research.DatasetCreated"
    DATASET_VERSION_CREATED = "research.DatasetVersionCreated"

    # --- Data Platform (SPEC-006 §7) ---
    DATASET_INDEXED = "research.DatasetIndexed"
    READ_MODEL_UPDATED = "research.ReadModelUpdated"

    # --- Alpha (SPEC-008 / SPEC-014) ---
    FEATURE_VERSION_CREATED = "alpha.FeatureVersionCreated"
    MODEL_TRAINED = "alpha.ModelTrained"
    MODEL_VALIDATED = "alpha.ModelValidated"
    ALPHA_GENERATED = "alpha.AlphaGenerated"

    # --- Decision (SPEC-010) ---
    RECOMMENDATION_CREATED = "decision.RecommendationCreated"
    CONFIDENCE_UPDATED = "decision.ConfidenceUpdated"
    TRADE_APPROVED = "decision.TradeApproved"
    TRADE_REJECTED = "decision.TradeRejected"

    # --- Portfolio (SPEC-011) ---
    REBALANCE_SUGGESTED = "portfolio.RebalanceSuggested"
    POSITION_UPDATED = "portfolio.PositionUpdated"

    # --- Execution (SPEC-013) ---
    ORDER_SUBMITTED = "execution.OrderSubmitted"
    ORDER_FILLED = "execution.OrderFilled"
    ORDER_CANCELLED = "execution.OrderCancelled"
    EXECUTION_QUALITY_UPDATED = "execution.ExecutionQualityUpdated"

    # --- Governance (SPEC-015) ---
    STRATEGY_PROMOTED = "governance.StrategyPromoted"
    STRATEGY_RETIRED = "governance.StrategyRetired"
    APPROVAL_GRANTED = "governance.ApprovalGranted"
    APPROVAL_REVOKED = "governance.ApprovalRevoked"

    @property
    def category(self) -> EventCategory:
        """The category derived from the event-type prefix, used for channel routing."""
        return EventCategory(self.value.split(".", 1)[0])
