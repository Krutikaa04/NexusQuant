"""Instrument Master repository (SPEC-004). Instruments are versioned, never mutated.

An update creates a new ``revision`` and flips the previous ``is_current`` flag off, so the
full metadata history is preserved and reproducible (SPEC-004 "Instrument master is
versioned").
"""

from __future__ import annotations

from uuid import uuid4

from sqlalchemy import select

from nexus_platform.db.repository import BaseRepository
from nexus_shared.primitives.time import utc_now
from market_intelligence.db.models import InstrumentRecord
from market_intelligence.domain.instruments import (
    Exchange,
    Instrument,
    ListingStatus,
    OptionType,
    Segment,
)


def _to_domain(row: InstrumentRecord) -> Instrument:
    return Instrument(
        symbol=row.symbol,
        exchange=Exchange(row.exchange),
        name=row.name,
        segment=Segment(row.segment),
        isin=row.isin,
        tick_size=row.tick_size,
        lot_size=row.lot_size,
        sector=row.sector,
        industry=row.industry,
        currency=row.currency,
        listing_status=ListingStatus(row.listing_status),
        expiry=row.expiry,
        strike=row.strike,
        option_type=OptionType(row.option_type) if row.option_type else None,
    )


class InstrumentRepository(BaseRepository[InstrumentRecord]):
    model = InstrumentRecord

    async def get_current_row(self, symbol: str, exchange: Exchange) -> InstrumentRecord | None:
        stmt = select(InstrumentRecord).where(
            InstrumentRecord.symbol == symbol,
            InstrumentRecord.exchange == exchange.value,
            InstrumentRecord.is_current.is_(True),
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_current(self, symbol: str, exchange: Exchange) -> Instrument | None:
        row = await self.get_current_row(symbol, exchange)
        return _to_domain(row) if row else None

    async def upsert(self, instrument: Instrument) -> tuple[Instrument, int]:
        """Create or supersede an instrument. Returns the stored instrument and its revision."""
        existing = await self.get_current_row(instrument.symbol, instrument.exchange)
        revision = 1
        if existing is not None:
            existing.is_current = False
            revision = existing.revision + 1
        record = InstrumentRecord(
            id=str(uuid4()),
            symbol=instrument.symbol,
            exchange=instrument.exchange.value,
            name=instrument.name,
            segment=instrument.segment.value,
            isin=instrument.isin,
            tick_size=instrument.tick_size,
            lot_size=instrument.lot_size,
            sector=instrument.sector,
            industry=instrument.industry,
            currency=instrument.currency,
            listing_status=instrument.listing_status.value,
            expiry=instrument.expiry,
            strike=instrument.strike,
            option_type=instrument.option_type.value if instrument.option_type else None,
            revision=revision,
            is_current=True,
            updated_at=utc_now(),
        )
        await self.add(record)
        return instrument, revision

    async def list_current(
        self, *, segment: Segment | None = None, exchange: Exchange | None = None
    ) -> list[Instrument]:
        stmt = select(InstrumentRecord).where(InstrumentRecord.is_current.is_(True))
        if segment is not None:
            stmt = stmt.where(InstrumentRecord.segment == segment.value)
        if exchange is not None:
            stmt = stmt.where(InstrumentRecord.exchange == exchange.value)
        stmt = stmt.order_by(InstrumentRecord.symbol.asc())
        rows = (await self.session.execute(stmt)).scalars().all()
        return [_to_domain(r) for r in rows]

    async def symbol_exists(self, symbol: str, exchange: Exchange) -> bool:
        return await self.get_current_row(symbol, exchange) is not None
