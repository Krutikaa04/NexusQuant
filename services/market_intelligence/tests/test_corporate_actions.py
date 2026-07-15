"""Corporate action adjustment tests (SPEC-004 Corporate Actions Engine)."""

from __future__ import annotations

from datetime import date

from nexus_shared.events.catalog import EventType
from market_intelligence.domain.corporate_actions import (
    CorporateAction,
    CorporateActionType,
    cumulative_factor,
)


def split(ex: date, ratio_from: int = 1, ratio_to: int = 10) -> CorporateAction:
    return CorporateAction(
        symbol="IRCTC", exchange="NSE", action_type=CorporateActionType.SPLIT,
        ex_date=ex, details={"ratio_from": ratio_from, "ratio_to": ratio_to},
    )


def test_split_factor() -> None:
    # 1:10 split — pre-split prices are divided by 10.
    assert split(date(2024, 6, 1)).price_factor() == 0.1


def test_bonus_factor() -> None:
    bonus = CorporateAction(
        symbol="X", exchange="NSE", action_type=CorporateActionType.BONUS,
        ex_date=date(2024, 6, 1), details={"ratio_from": 1, "ratio_to": 1},
    )
    assert bonus.price_factor() == 0.5  # 1:1 bonus halves the price


def test_dividend_factor_uses_reference_price() -> None:
    dividend = CorporateAction(
        symbol="X", exchange="NSE", action_type=CorporateActionType.DIVIDEND,
        ex_date=date(2024, 6, 1), details={"amount": 10.0},
    )
    assert dividend.price_factor(reference_price=200.0) == 0.95


def test_cumulative_factor_only_applies_before_ex_date() -> None:
    actions = [split(date(2024, 6, 1))]
    assert cumulative_factor(actions, date(2024, 5, 31)) == 0.1  # before ex-date: adjusted
    assert cumulative_factor(actions, date(2024, 6, 1)) == 1.0  # on/after: raw


def test_cumulative_factor_compounds() -> None:
    actions = [split(date(2024, 6, 1), 1, 10), split(date(2024, 8, 1), 1, 2)]
    assert abs(cumulative_factor(actions, date(2024, 5, 1)) - 0.05) < 1e-12
    assert cumulative_factor(actions, date(2024, 7, 1)) == 0.5


async def test_service_records_and_publishes(container, publisher) -> None:
    version = await container.corporate_actions.record(split(date(2024, 6, 1)))
    assert version == 1
    # Idempotent: identical action returns the same version.
    assert await container.corporate_actions.record(split(date(2024, 6, 1))) == 1
    # A later distinct action bumps the per-symbol version.
    assert await container.corporate_actions.record(split(date(2024, 9, 1), 1, 2)) == 2

    events = publisher.of_type(EventType.CORPORATE_ACTION_APPLIED)
    assert len(events) == 2  # idempotent re-record does not re-publish
    assert events[0].payload["adjustment_version"] == 1
