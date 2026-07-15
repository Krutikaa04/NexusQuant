"""Payload contracts for the market events this context publishes (SPEC-004 Domain Events).

Registered with the shared schema registry so the Event Fabric validates them at publish
time and downstream consumers have a versioned contract to code against.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from nexus_shared.events.catalog import EventType
from nexus_shared.events.registry import default_registry


class TickReceivedPayload(BaseModel):
    symbol: str
    exchange: str
    ltp: float
    ltq: int
    volume: int
    sequence: int
    bid: float | None = None
    ask: float | None = None
    quality_score: float
    exchange_ts: datetime


class CandleClosedPayload(BaseModel):
    symbol: str
    interval_seconds: int
    open_time: datetime
    close_time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    tick_count: int


class DataQualityChangedPayload(BaseModel):
    symbol: str
    score: float
    confidence: str
    readiness: str
    metrics: dict = Field(default_factory=dict)


class InstrumentUpdatedPayload(BaseModel):
    symbol: str
    exchange: str
    segment: str
    revision: int
    listing_status: str


class MarketRegimeChangedPayload(BaseModel):
    symbol: str
    regimes: list[str]
    indicators: dict = Field(default_factory=dict)


class CorporateActionAppliedPayload(BaseModel):
    symbol: str
    exchange: str
    action_type: str
    ex_date: str
    details: dict = Field(default_factory=dict)
    adjustment_version: int


class TradingSessionPayload(BaseModel):
    exchange: str
    at: datetime
    phase: str


def register_published_schemas() -> None:
    default_registry.register(EventType.TICK_RECEIVED, 1, TickReceivedPayload)
    default_registry.register(EventType.CANDLE_CLOSED, 1, CandleClosedPayload)
    default_registry.register(EventType.DATA_QUALITY_CHANGED, 1, DataQualityChangedPayload)
    default_registry.register(EventType.INSTRUMENT_UPDATED, 1, InstrumentUpdatedPayload)
    default_registry.register(EventType.MARKET_REGIME_CHANGED, 1, MarketRegimeChangedPayload)
    default_registry.register(
        EventType.CORPORATE_ACTION_APPLIED, 1, CorporateActionAppliedPayload
    )
    default_registry.register(EventType.TRADING_SESSION_OPENED, 1, TradingSessionPayload)
    default_registry.register(EventType.TRADING_SESSION_CLOSED, 1, TradingSessionPayload)
