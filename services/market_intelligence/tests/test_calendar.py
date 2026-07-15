"""Trading calendar unit tests (SPEC-004 Trading Calendar)."""

from __future__ import annotations

from datetime import date, datetime, time

from market_intelligence.domain.calendar import (
    IST,
    Holiday,
    SessionKind,
    SessionPhase,
    SpecialSession,
    TradingCalendar,
)

# 2024-01-26 (Republic Day, Friday) is a real NSE holiday.
REPUBLIC_DAY = Holiday(day=date(2024, 1, 26), reason="Republic Day")
CAL = TradingCalendar(holidays=[REPUBLIC_DAY])


def test_weekday_is_trading_day() -> None:
    assert CAL.is_trading_day(date(2024, 1, 22))  # Monday


def test_weekend_is_not_trading_day() -> None:
    assert not CAL.is_trading_day(date(2024, 1, 20))  # Saturday
    assert not CAL.is_trading_day(date(2024, 1, 21))  # Sunday


def test_holiday_is_not_trading_day() -> None:
    assert not CAL.is_trading_day(REPUBLIC_DAY.day)
    assert CAL.is_holiday(REPUBLIC_DAY.day)


def test_muhurat_special_session_trades_on_holiday() -> None:
    muhurat = SpecialSession(
        day=date(2024, 11, 1),  # Diwali (Friday, market holiday)
        kind=SessionKind.MUHURAT,
        open_time=time(18, 0),
        close_time=time(19, 0),
        description="Muhurat Trading",
    )
    cal = TradingCalendar(
        holidays=[Holiday(day=date(2024, 11, 1), reason="Diwali")],
        special_sessions=[muhurat],
    )
    assert cal.is_trading_day(date(2024, 11, 1))
    assert cal.session_window(date(2024, 11, 1)) == (time(18, 0), time(19, 0))


def test_session_phases_through_the_day() -> None:
    monday = date(2024, 1, 22)

    def at(h: int, m: int) -> datetime:
        return datetime(monday.year, monday.month, monday.day, h, m, tzinfo=IST)

    assert CAL.phase_at(at(8, 0)) is SessionPhase.CLOSED
    assert CAL.phase_at(at(9, 5)) is SessionPhase.PRE_OPEN
    assert CAL.phase_at(at(10, 0)) is SessionPhase.OPEN
    assert CAL.phase_at(at(15, 29)) is SessionPhase.OPEN
    assert CAL.phase_at(at(15, 30)) is SessionPhase.POST_CLOSE


def test_next_trading_day_skips_weekend_and_holiday() -> None:
    # Thursday 2024-01-25 -> Friday is Republic Day, weekend follows -> Monday 29th.
    assert CAL.next_trading_day(date(2024, 1, 25)) == date(2024, 1, 29)


def test_weekly_expiry_is_thursday() -> None:
    assert CAL.weekly_expiry(date(2024, 1, 22)) == date(2024, 1, 25)  # that week's Thursday
    assert CAL.weekly_expiry(date(2024, 1, 25)) == date(2024, 1, 25)  # expiry day itself


def test_weekly_expiry_rolls_back_on_holiday() -> None:
    cal = TradingCalendar(holidays=[Holiday(day=date(2024, 1, 25), reason="Test holiday")])
    # Thursday 25th is a holiday -> expiry moves to Wednesday 24th.
    assert cal.weekly_expiry(date(2024, 1, 22)) == date(2024, 1, 24)


def test_monthly_expiry_is_last_thursday() -> None:
    assert CAL.monthly_expiry(2024, 1) == date(2024, 1, 25)
    assert CAL.monthly_expiry(2024, 2) == date(2024, 2, 29)  # leap-year February
