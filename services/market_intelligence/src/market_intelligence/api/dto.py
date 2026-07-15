"""Request/response models for the Market Intelligence API (SPEC-004 Public APIs)."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field

from market_intelligence.domain.corporate_actions import (
    CorporateAction,
    CorporateActionType,
)
from market_intelligence.domain.instruments import (
    Exchange,
    Instrument,
    ListingStatus,
    OptionType,
    Segment,
)


class HealthResponse(BaseModel):
    status: str
    service: str
    environment: str
    migrations_applied: list[str]


class InstrumentBody(BaseModel):
    """Upsert payload for an instrument (SPEC-004 Instrument Master)."""

    symbol: str = Field(min_length=1)
    exchange: Exchange = Exchange.NSE
    name: str = Field(min_length=1)
    segment: Segment = Segment.EQUITY
    isin: str | None = None
    tick_size: float = 0.05
    lot_size: int = Field(default=1, ge=1)
    sector: str | None = None
    industry: str | None = None
    currency: str = "INR"
    listing_status: ListingStatus = ListingStatus.LISTED
    expiry: date | None = None
    strike: float | None = None
    option_type: OptionType | None = None

    def to_domain(self) -> Instrument:
        return Instrument(
            symbol=self.symbol,
            exchange=self.exchange,
            name=self.name,
            segment=self.segment,
            isin=self.isin,
            tick_size=self.tick_size,
            lot_size=self.lot_size,
            sector=self.sector,
            industry=self.industry,
            currency=self.currency,
            listing_status=self.listing_status,
            expiry=self.expiry,
            strike=self.strike,
            option_type=self.option_type,
        )


class InstrumentUpsertResponse(BaseModel):
    symbol: str
    exchange: Exchange
    revision: int


class MockIngestBody(BaseModel):
    """Trigger the development-mode synthetic feed through the ingestion pipeline."""

    symbols: dict[str, float] = Field(
        default_factory=lambda: {"RELIANCE": 2950.0, "TCS": 3900.0, "INFY": 1500.0}
    )
    count: int = Field(default=300, ge=1, le=100_000)
    exchange: Exchange = Exchange.NSE
    seed: int = 42


class IngestResultResponse(BaseModel):
    accepted: int
    rejected: int
    candles_closed: int
    quality_changes: int
    events_published: int
    rejections: dict[str, int]


class ReplayResponse(BaseModel):
    symbol: str
    replayed: int
    published: bool


class HolidayBody(BaseModel):
    day: date
    reason: str = Field(min_length=1)


class CorporateActionBody(BaseModel):
    symbol: str = Field(min_length=1)
    exchange: Exchange = Exchange.NSE
    action_type: CorporateActionType
    ex_date: date
    details: dict = Field(default_factory=dict)

    def to_domain(self) -> CorporateAction:
        return CorporateAction(
            symbol=self.symbol,
            exchange=self.exchange.value,
            action_type=self.action_type,
            ex_date=self.ex_date,
            details=self.details,
        )
