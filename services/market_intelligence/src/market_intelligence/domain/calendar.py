"""Trading calendar domain (SPEC-004 Trading Calendar).

Encodes NSE session structure: regular Monday–Friday trading, exchange holidays, special
sessions (e.g. Muhurat), pre-open, and derivative expiries (weekly/monthly Thursday, with
holiday roll-back). All rules are pure functions over injected holiday data so the
calendar is deterministic and testable.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from enum import Enum

IST = timezone(timedelta(hours=5, minutes=30))

# NSE equity session times (IST).
PRE_OPEN_START = time(9, 0)
PRE_OPEN_END = time(9, 8)
SESSION_OPEN = time(9, 15)
SESSION_CLOSE = time(15, 30)


class SessionKind(str, Enum):
    REGULAR = "regular"
    MUHURAT = "muhurat"
    SPECIAL = "special"


class SessionPhase(str, Enum):
    CLOSED = "closed"
    PRE_OPEN = "pre_open"
    OPEN = "open"
    POST_CLOSE = "post_close"


@dataclass(frozen=True, slots=True)
class Holiday:
    day: date
    reason: str


@dataclass(frozen=True, slots=True)
class SpecialSession:
    """A non-regular trading window (e.g. Muhurat trading on Diwali)."""

    day: date
    kind: SessionKind
    open_time: time
    close_time: time
    description: str


class TradingCalendar:
    def __init__(
        self,
        holidays: list[Holiday] | None = None,
        special_sessions: list[SpecialSession] | None = None,
    ) -> None:
        self._holidays = {h.day: h for h in (holidays or [])}
        self._special = {s.day: s for s in (special_sessions or [])}

    def is_holiday(self, day: date) -> bool:
        return day in self._holidays

    def is_trading_day(self, day: date) -> bool:
        if day in self._special:  # special sessions trade even on holidays/weekends
            return True
        return day.weekday() < 5 and day not in self._holidays

    def session_window(self, day: date) -> tuple[time, time] | None:
        """The (open, close) times for a day, or None when the market is shut."""
        special = self._special.get(day)
        if special is not None:
            return special.open_time, special.close_time
        if not self.is_trading_day(day):
            return None
        return SESSION_OPEN, SESSION_CLOSE

    def phase_at(self, moment: datetime) -> SessionPhase:
        """The session phase at an instant (any tz; evaluated in IST)."""
        local = moment.astimezone(IST)
        window = self.session_window(local.date())
        if window is None:
            return SessionPhase.CLOSED
        open_t, close_t = window
        now = local.time()
        if local.date() not in self._special and PRE_OPEN_START <= now < PRE_OPEN_END:
            return SessionPhase.PRE_OPEN
        if open_t <= now < close_t:
            return SessionPhase.OPEN
        if now >= close_t:
            return SessionPhase.POST_CLOSE
        return SessionPhase.CLOSED

    def next_trading_day(self, day: date) -> date:
        candidate = day + timedelta(days=1)
        while not self.is_trading_day(candidate):
            candidate += timedelta(days=1)
        return candidate

    # --- Expiries (SPEC-004: weekly / monthly expiry) ---

    def weekly_expiry(self, from_day: date) -> date:
        """The next weekly derivatives expiry: Thursday, rolled back on holidays."""
        candidate = from_day + timedelta(days=(3 - from_day.weekday()) % 7)  # next Thursday
        while not self.is_trading_day(candidate):
            candidate -= timedelta(days=1)  # holiday => previous trading day
        if candidate < from_day:  # rolled past today; use next week's
            return self.weekly_expiry(from_day + timedelta(days=7))
        return candidate

    def monthly_expiry(self, year: int, month: int) -> date:
        """The monthly expiry: last Thursday of the month, rolled back on holidays."""
        if month == 12:
            last = date(year, 12, 31)
        else:
            last = date(year, month + 1, 1) - timedelta(days=1)
        candidate = last - timedelta(days=(last.weekday() - 3) % 7)  # last Thursday
        while not self.is_trading_day(candidate):
            candidate -= timedelta(days=1)
        return candidate
