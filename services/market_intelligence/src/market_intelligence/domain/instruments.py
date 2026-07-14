"""Instrument Master domain types (SPEC-004 Instrument Master)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum


class Exchange(str, Enum):
    NSE = "NSE"
    BSE = "BSE"


class Segment(str, Enum):
    """Market segment. Indian equity market instruments span cash and derivatives."""

    EQUITY = "EQ"
    FUTURES = "FUT"
    OPTIONS = "OPT"
    INDEX = "INDEX"
    ETF = "ETF"


class OptionType(str, Enum):
    CALL = "CE"
    PUT = "PE"


class ListingStatus(str, Enum):
    LISTED = "listed"
    SUSPENDED = "suspended"
    DELISTED = "delisted"


@dataclass(frozen=True, slots=True)
class Instrument:
    """Canonical, immutable-per-version instrument metadata (SPEC-004)."""

    symbol: str
    exchange: Exchange
    name: str
    segment: Segment
    isin: str | None = None
    tick_size: float = 0.05
    lot_size: int = 1
    sector: str | None = None
    industry: str | None = None
    currency: str = "INR"
    listing_status: ListingStatus = ListingStatus.LISTED
    # Derivatives-only attributes.
    expiry: date | None = None
    strike: float | None = None
    option_type: OptionType | None = None

    @property
    def is_tradable(self) -> bool:
        return self.listing_status is ListingStatus.LISTED
