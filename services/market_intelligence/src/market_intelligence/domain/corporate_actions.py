"""Corporate actions domain (SPEC-004 Corporate Actions Engine).

Historical candles are immutable, so corporate actions never rewrite them. Instead each
action contributes a *versioned adjustment factor*; adjusted prices are computed on read
by multiplying raw prices by the cumulative factor of all actions with an ex-date after
the bar. This keeps every historical dataset reproducible (SPEC-004: "Historical datasets
remain reproducible by versioning adjustments") — a research artifact can pin either raw
or adjusted-as-of-version data.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum


class CorporateActionType(str, Enum):
    DIVIDEND = "dividend"
    SPLIT = "split"
    BONUS = "bonus"
    RIGHTS = "rights"
    MERGER = "merger"
    DEMERGER = "demerger"
    SYMBOL_CHANGE = "symbol_change"


@dataclass(frozen=True, slots=True)
class CorporateAction:
    symbol: str
    exchange: str
    action_type: CorporateActionType
    ex_date: date
    # Type-specific terms, e.g. {"ratio_from": 1, "ratio_to": 10} for a 1:10 split,
    # {"amount": 9.0} for a dividend, {"new_symbol": "X"} for a symbol change.
    details: dict

    def price_factor(self, reference_price: float | None = None) -> float:
        """The multiplicative factor applied to prices *before* the ex-date.

        SPLIT  1:N  -> factor 1/N (a pre-split price is N times the post-split price).
        BONUS  A:B  -> holders of B shares receive A extra: factor B/(A+B).
        DIVIDEND    -> factor (P - D) / P against the pre-ex reference price.
        Other action types do not adjust prices.
        """
        t = self.action_type
        if t is CorporateActionType.SPLIT:
            ratio_from = float(self.details["ratio_from"])
            ratio_to = float(self.details["ratio_to"])
            return ratio_from / ratio_to
        if t is CorporateActionType.BONUS:
            bonus = float(self.details["ratio_from"])  # A new shares ...
            held = float(self.details["ratio_to"])  # ... per B held
            return held / (bonus + held)
        if t is CorporateActionType.DIVIDEND and reference_price:
            amount = float(self.details["amount"])
            return max(0.0, (reference_price - amount) / reference_price)
        return 1.0


def cumulative_factor(
    actions: list[CorporateAction], bar_date: date, *, reference_price: float | None = None
) -> float:
    """Cumulative adjustment for a bar dated ``bar_date``: product of the factors of all
    actions whose ex-date falls strictly after the bar."""
    factor = 1.0
    for action in actions:
        if action.ex_date > bar_date:
            factor *= action.price_factor(reference_price)
    return factor
