"""Calendar, corporate-action, and regime services (SPEC-004 subsystems).

Each service is a thin transaction + event boundary over pure domain logic:

* ``CalendarService`` — persists holidays/special sessions, answers calendar queries, and
  publishes ``TradingSessionOpened``/``TradingSessionClosed`` on observed phase
  transitions (evaluation is an explicit call, so it is deterministic and schedulable).
* ``CorporateActionService`` — records versioned actions (publishing
  ``CorporateActionApplied``) and serves *adjusted* candles computed on read; stored
  candles are never mutated (SPEC-004 reproducibility).
* ``RegimeService`` — classifies the market from stored candles and publishes
  ``MarketRegimeChanged`` when the regime set changes.
"""

from __future__ import annotations

from datetime import date, datetime

from nexus_shared.events.catalog import EventType
from nexus_shared.events.envelope import EventEnvelope
from nexus_shared.events.publisher import EventPublisher
from nexus_platform.db.session import Database
from market_intelligence.domain.calendar import (
    Holiday,
    SessionPhase,
    SpecialSession,
    TradingCalendar,
)
from market_intelligence.domain.candles import Interval
from market_intelligence.domain.corporate_actions import CorporateAction, cumulative_factor
from market_intelligence.domain.regime import RegimeClassifier
from market_intelligence.ingestion.pipeline import PRODUCER
from market_intelligence.repositories.market_data import MarketDataRepository
from market_intelligence.repositories.reference import ReferenceDataRepository


class CalendarService:
    def __init__(self, database: Database, publisher: EventPublisher) -> None:
        self._db = database
        self._publisher = publisher
        self._last_phase: SessionPhase | None = None

    async def load(self) -> TradingCalendar:
        async with self._db.session() as session:
            repo = ReferenceDataRepository(session)
            return TradingCalendar(
                holidays=await repo.load_holidays(),
                special_sessions=await repo.load_special_sessions(),
            )

    async def add_holiday(self, holiday: Holiday) -> None:
        async with self._db.begin() as session:
            await ReferenceDataRepository(session).add_holiday(holiday)

    async def add_special_session(self, special: SpecialSession) -> None:
        async with self._db.begin() as session:
            await ReferenceDataRepository(session).add_special_session(special)

    async def evaluate_phase(self, moment: datetime) -> SessionPhase:
        """Evaluate the session phase at ``moment``; publish open/close on transitions."""
        calendar = await self.load()
        phase = calendar.phase_at(moment)
        previous, self._last_phase = self._last_phase, phase
        if previous is not None and previous != phase:
            if phase is SessionPhase.OPEN:
                await self._publish_session_event(EventType.TRADING_SESSION_OPENED, moment, phase)
            elif previous is SessionPhase.OPEN:
                await self._publish_session_event(EventType.TRADING_SESSION_CLOSED, moment, phase)
        return phase

    async def _publish_session_event(
        self, event_type: EventType, moment: datetime, phase: SessionPhase
    ) -> None:
        await self._publisher.publish(
            EventEnvelope(
                event_type=event_type,
                producer=PRODUCER,
                aggregate_id="NSE",
                payload={"exchange": "NSE", "at": moment.isoformat(), "phase": phase.value},
            )
        )


class CorporateActionService:
    def __init__(self, database: Database, publisher: EventPublisher) -> None:
        self._db = database
        self._publisher = publisher

    async def record(self, action: CorporateAction) -> int:
        async with self._db.begin() as session:
            version, created = await ReferenceDataRepository(session).add_corporate_action(
                action
            )
        if created:  # idempotent re-record must not re-publish
            await self._publisher.publish(
                EventEnvelope(
                    event_type=EventType.CORPORATE_ACTION_APPLIED,
                    producer=PRODUCER,
                    aggregate_id=action.symbol,
                    payload={
                        "symbol": action.symbol,
                        "exchange": action.exchange,
                        "action_type": action.action_type.value,
                        "ex_date": action.ex_date.isoformat(),
                        "details": action.details,
                        "adjustment_version": version,
                    },
                )
            )
        return version

    async def list_for(self, symbol: str, exchange: str) -> list[CorporateAction]:
        async with self._db.session() as session:
            return await ReferenceDataRepository(session).corporate_actions_for(symbol, exchange)

    async def adjusted_candles(
        self,
        symbol: str,
        exchange: str,
        interval: Interval,
        *,
        since: datetime | None = None,
        limit: int = 500,
        up_to_version: int | None = None,
    ) -> list[dict]:
        """Candles with corporate-action adjustment applied on read.

        ``up_to_version`` pins the adjustment state, making any historical query exactly
        reproducible regardless of actions recorded later (SPEC-004 acceptance criteria).
        """
        async with self._db.session() as session:
            repo = ReferenceDataRepository(session)
            actions = await repo.corporate_actions_for(
                symbol, exchange, up_to_version=up_to_version
            )
            rows = await MarketDataRepository(session).get_candles(
                symbol, interval, since=since, limit=limit
            )
        out = []
        for r in rows:
            factor = cumulative_factor(actions, r.open_time.date(), reference_price=r.close)
            out.append(
                {
                    "symbol": r.symbol,
                    "open_time": r.open_time.isoformat(),
                    "close_time": r.close_time.isoformat(),
                    "open": round(r.open * factor, 4),
                    "high": round(r.high * factor, 4),
                    "low": round(r.low * factor, 4),
                    "close": round(r.close * factor, 4),
                    "volume": r.volume,
                    "tick_count": r.tick_count,
                    "adjustment_factor": round(factor, 8),
                }
            )
        return out


class RegimeService:
    def __init__(
        self,
        database: Database,
        publisher: EventPublisher,
        calendar_service: CalendarService,
        *,
        classifier: RegimeClassifier | None = None,
        interval: Interval = Interval.ONE_MINUTE,
    ) -> None:
        self._db = database
        self._publisher = publisher
        self._calendar = calendar_service
        self._classifier = classifier or RegimeClassifier()
        self._interval = interval

    async def assess(self, symbol: str, *, as_of: datetime | None = None) -> dict | None:
        """Classify the current regime from stored candles; persist + publish on change."""
        async with self._db.session() as session:
            rows = await MarketDataRepository(session).get_candles(
                symbol, self._interval, limit=self._classifier.min_bars * 3
            )
        closes = [r.close for r in rows]
        expiry_week = False
        if as_of is not None:
            calendar = await self._calendar.load()
            today: date = as_of.date()
            expiry_week = (calendar.weekly_expiry(today) - today).days < 5

        assessment = self._classifier.classify(symbol, closes, expiry_week=expiry_week)
        if assessment is None:
            return None

        async with self._db.begin() as session:
            repo = ReferenceDataRepository(session)
            latest = await repo.latest_regime(symbol)
            new_regimes = [r.value for r in assessment.regimes]
            changed = latest is None or latest.regimes != new_regimes
            if changed:
                await repo.append_regime(assessment)

        if changed:
            await self._publisher.publish(
                EventEnvelope(
                    event_type=EventType.MARKET_REGIME_CHANGED,
                    producer=PRODUCER,
                    aggregate_id=symbol,
                    payload={
                        "symbol": symbol,
                        "regimes": new_regimes,
                        "indicators": assessment.indicators,
                    },
                )
            )
        return {"symbol": symbol, "regimes": new_regimes, "indicators": assessment.indicators,
                "changed": changed}

    async def current(self, symbol: str) -> dict | None:
        async with self._db.session() as session:
            row = await ReferenceDataRepository(session).latest_regime(symbol)
        if row is None:
            return None
        return {
            "symbol": row.symbol,
            "regimes": row.regimes,
            "indicators": row.indicators,
            "as_of": row.created_at.isoformat(),
        }
