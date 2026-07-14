"""Instrument Master service (SPEC-004 Instrument Master).

Owns instrument registration. An upsert versions the instrument, registers its symbol with
the ingestion pipeline (so its ticks pass symbol validation), and publishes
``InstrumentUpdated``.
"""

from __future__ import annotations

from nexus_shared.events.catalog import EventType
from nexus_shared.events.envelope import EventEnvelope
from nexus_shared.events.publisher import EventPublisher
from nexus_platform.db.session import Database
from market_intelligence.domain.instruments import Exchange, Instrument, Segment
from market_intelligence.ingestion.pipeline import PRODUCER, IngestionPipeline
from market_intelligence.repositories.instruments import InstrumentRepository


class InstrumentService:
    def __init__(
        self, database: Database, publisher: EventPublisher, pipeline: IngestionPipeline
    ) -> None:
        self._db = database
        self._publisher = publisher
        self._pipeline = pipeline

    async def upsert(self, instrument: Instrument) -> int:
        async with self._db.begin() as session:
            _, revision = await InstrumentRepository(session).upsert(instrument)
        self._pipeline.register_symbol(instrument.symbol, instrument.exchange.value)
        await self._publisher.publish(
            EventEnvelope(
                event_type=EventType.INSTRUMENT_UPDATED,
                producer=PRODUCER,
                aggregate_id=f"{instrument.exchange.value}:{instrument.symbol}",
                payload={
                    "symbol": instrument.symbol,
                    "exchange": instrument.exchange.value,
                    "segment": instrument.segment.value,
                    "revision": revision,
                    "listing_status": instrument.listing_status.value,
                },
            )
        )
        return revision

    async def get(self, symbol: str, exchange: Exchange) -> Instrument | None:
        async with self._db.session() as session:
            return await InstrumentRepository(session).get_current(symbol, exchange)

    async def list(
        self, *, segment: Segment | None = None, exchange: Exchange | None = None
    ) -> list[Instrument]:
        async with self._db.session() as session:
            return await InstrumentRepository(session).list_current(
                segment=segment, exchange=exchange
            )

    async def load_known_symbols(self) -> None:
        """Prime the pipeline's symbol set from the persisted instrument master (startup)."""
        instruments = await self.list()
        self._pipeline.sync_known_symbols(
            [(i.symbol, i.exchange.value) for i in instruments]
        )
