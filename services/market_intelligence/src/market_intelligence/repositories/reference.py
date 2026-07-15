"""Reference-data repository: calendar, corporate actions, regimes (SPEC-004)."""

from __future__ import annotations

from datetime import date, time
from uuid import uuid4

from sqlalchemy import func, select

from nexus_platform.db.repository import BaseRepository
from nexus_shared.primitives.time import utc_now
from market_intelligence.db.models import (
    CorporateActionRecord,
    HolidayRecord,
    RegimeRecord,
    SpecialSessionRecord,
)
from market_intelligence.domain.calendar import Holiday, SessionKind, SpecialSession
from market_intelligence.domain.corporate_actions import CorporateAction, CorporateActionType
from market_intelligence.domain.regime import RegimeAssessment


class ReferenceDataRepository(BaseRepository[HolidayRecord]):
    model = HolidayRecord

    # --- calendar ---

    async def add_holiday(self, holiday: Holiday) -> None:
        if await self.session.get(HolidayRecord, holiday.day) is None:
            self.session.add(HolidayRecord(day=holiday.day, reason=holiday.reason))

    async def add_special_session(self, special: SpecialSession) -> None:
        if await self.session.get(SpecialSessionRecord, special.day) is None:
            self.session.add(
                SpecialSessionRecord(
                    day=special.day,
                    kind=special.kind.value,
                    open_time=special.open_time.strftime("%H:%M"),
                    close_time=special.close_time.strftime("%H:%M"),
                    description=special.description,
                )
            )

    async def load_holidays(self) -> list[Holiday]:
        rows = (await self.session.execute(select(HolidayRecord))).scalars().all()
        return [Holiday(day=r.day, reason=r.reason) for r in rows]

    async def load_special_sessions(self) -> list[SpecialSession]:
        rows = (await self.session.execute(select(SpecialSessionRecord))).scalars().all()
        return [
            SpecialSession(
                day=r.day,
                kind=SessionKind(r.kind),
                open_time=time.fromisoformat(r.open_time),
                close_time=time.fromisoformat(r.close_time),
                description=r.description,
            )
            for r in rows
        ]

    # --- corporate actions ---

    async def add_corporate_action(self, action: CorporateAction) -> tuple[int, bool]:
        """Append a corporate action, assigning the next per-symbol adjustment version.

        Returns ``(version, created)``; re-adding an identical action returns the existing
        version with ``created=False`` (idempotent).
        """
        existing = (
            await self.session.execute(
                select(CorporateActionRecord).where(
                    CorporateActionRecord.symbol == action.symbol,
                    CorporateActionRecord.exchange == action.exchange,
                    CorporateActionRecord.action_type == action.action_type.value,
                    CorporateActionRecord.ex_date == action.ex_date,
                )
            )
        ).scalar_one_or_none()
        if existing is not None:
            return existing.adjustment_version, False

        current = (
            await self.session.execute(
                select(func.max(CorporateActionRecord.adjustment_version)).where(
                    CorporateActionRecord.symbol == action.symbol,
                    CorporateActionRecord.exchange == action.exchange,
                )
            )
        ).scalar_one_or_none()
        version = (current or 0) + 1
        self.session.add(
            CorporateActionRecord(
                id=str(uuid4()),
                symbol=action.symbol,
                exchange=action.exchange,
                action_type=action.action_type.value,
                ex_date=action.ex_date,
                details=action.details,
                adjustment_version=version,
                created_at=utc_now(),
            )
        )
        await self.session.flush()
        return version, True

    async def corporate_actions_for(
        self, symbol: str, exchange: str, *, up_to_version: int | None = None
    ) -> list[CorporateAction]:
        stmt = select(CorporateActionRecord).where(
            CorporateActionRecord.symbol == symbol,
            CorporateActionRecord.exchange == exchange,
        )
        if up_to_version is not None:
            stmt = stmt.where(CorporateActionRecord.adjustment_version <= up_to_version)
        stmt = stmt.order_by(CorporateActionRecord.ex_date.asc())
        rows = (await self.session.execute(stmt)).scalars().all()
        return [
            CorporateAction(
                symbol=r.symbol,
                exchange=r.exchange,
                action_type=CorporateActionType(r.action_type),
                ex_date=r.ex_date,
                details=r.details,
            )
            for r in rows
        ]

    # --- regimes ---

    async def append_regime(self, assessment: RegimeAssessment) -> None:
        self.session.add(
            RegimeRecord(
                symbol=assessment.symbol,
                regimes=[r.value for r in assessment.regimes],
                indicators=assessment.indicators,
                created_at=utc_now(),
            )
        )

    async def latest_regime(self, symbol: str) -> RegimeRecord | None:
        stmt = (
            select(RegimeRecord)
            .where(RegimeRecord.symbol == symbol)
            .order_by(RegimeRecord.created_at.desc(), RegimeRecord.id.desc())
            .limit(1)
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()
