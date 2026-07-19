"""DhanHQ (v2) market-data provider — pure mapping helpers.

Network I/O lives in the composing application (the BFF); this module holds only pure,
deterministic, testable functions so the provider integration can be verified without a
live token. Two responsibilities:

1. ``resolve_security_ids`` — map our canonical universe symbols to Dhan security IDs by
   parsing the published security-master CSV. Robust to the compact/detailed column naming.
2. ``quote_response_to_ticks`` — convert a ``/v2/marketfeed/quote`` response into canonical
   :class:`RawTick`s. No downstream code ever sees the raw Dhan payload — it is converted to
   the domain type at this boundary, exactly like any other vendor adapter.

Dhan API segment codes used: ``NSE_EQ`` for cash equities, ``IDX_I`` for indices.
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from datetime import datetime

from market_intelligence.domain.ticks import RawTick

DHAN_QUOTE_URL = "https://api.dhan.co/v2/marketfeed/quote"
DHAN_SCRIP_MASTER_URL = "https://images.dhan.co/api-data/api-scrip-master.csv"


@dataclass(frozen=True, slots=True)
class DhanInstrument:
    """A resolved mapping from our canonical symbol to a Dhan (segment, security_id)."""

    symbol: str        # our canonical symbol, e.g. "RELIANCE", "NIFTY50"
    segment: str       # Dhan API exchange segment: "NSE_EQ" | "IDX_I"
    security_id: str


@dataclass(frozen=True, slots=True)
class DhanSymbolSpec:
    """How to find one of our symbols in the security master."""

    symbol: str
    segment: str                 # target Dhan API segment
    candidates: tuple[str, ...]  # acceptable trading/custom names (case-insensitive)


# The seeded NSE universe (mirrors apps/backend/seed.py). Equity trading symbols match the
# NSE symbol; index custom names vary, so several candidates are provided.
DEFAULT_UNIVERSE: tuple[DhanSymbolSpec, ...] = (
    DhanSymbolSpec("RELIANCE", "NSE_EQ", ("RELIANCE",)),
    DhanSymbolSpec("TCS", "NSE_EQ", ("TCS",)),
    DhanSymbolSpec("INFY", "NSE_EQ", ("INFY",)),
    DhanSymbolSpec("HDFCBANK", "NSE_EQ", ("HDFCBANK",)),
    DhanSymbolSpec("ICICIBANK", "NSE_EQ", ("ICICIBANK",)),
    DhanSymbolSpec("SBIN", "NSE_EQ", ("SBIN",)),
    DhanSymbolSpec("BHARTIARTL", "NSE_EQ", ("BHARTIARTL",)),
    DhanSymbolSpec("ITC", "NSE_EQ", ("ITC",)),
    DhanSymbolSpec("NIFTY50", "IDX_I", ("NIFTY 50", "NIFTY", "NIFTY50")),
    DhanSymbolSpec("NIFTYBANK", "IDX_I", ("NIFTY BANK", "BANKNIFTY", "NIFTY BANK INDEX")),
    DhanSymbolSpec("NIFTYIT", "IDX_I", ("NIFTY IT", "NIFTYIT")),
)


def _find_cols(header: list[str], *needles: str) -> list[int]:
    """Indices of header cells whose upper-cased name contains any needle."""
    up = [h.upper() for h in header]
    return [i for i, h in enumerate(up) if any(n in h for n in needles)]


def resolve_security_ids(
    csv_text: str, specs: tuple[DhanSymbolSpec, ...] = DEFAULT_UNIVERSE
) -> tuple[dict[tuple[str, str], DhanInstrument], list[str]]:
    """Parse the security-master CSV and resolve each spec to a security id.

    Returns ``(by_key, unresolved)`` where ``by_key`` is keyed by ``(segment, security_id)``
    (the shape a quote response is indexed by) and ``unresolved`` lists symbols not found so
    the caller can surface them explicitly rather than silently dropping instruments.
    """
    reader = csv.reader(io.StringIO(csv_text))
    try:
        header = next(reader)
    except StopIteration:
        return {}, [s.symbol for s in specs]

    id_cols = _find_cols(header, "SECURITY_ID")
    name_cols = _find_cols(header, "SYMBOL", "DISPLAY_NAME", "CUSTOM")
    if not id_cols or not name_cols:
        return {}, [s.symbol for s in specs]
    id_col = id_cols[0]

    # Build name(upper) -> security_id from the whole file (first occurrence wins).
    name_to_id: dict[str, str] = {}
    for row in reader:
        if len(row) <= id_col:
            continue
        sec_id = (row[id_col] or "").strip()
        if not sec_id:
            continue
        for c in name_cols:
            if c < len(row):
                key = (row[c] or "").strip().upper()
                if key and key not in name_to_id:
                    name_to_id[key] = sec_id

    resolved: dict[tuple[str, str], DhanInstrument] = {}
    unresolved: list[str] = []
    for spec in specs:
        sec_id = next((name_to_id[c.upper()] for c in spec.candidates if c.upper() in name_to_id), None)
        if sec_id is None:
            unresolved.append(spec.symbol)
            continue
        resolved[(spec.segment, sec_id)] = DhanInstrument(spec.symbol, spec.segment, sec_id)
    return resolved, unresolved


def request_groups(by_key: dict[tuple[str, str], DhanInstrument]) -> dict[str, list[int]]:
    """Group resolved security ids by segment for a /marketfeed/quote request body."""
    groups: dict[str, list[int]] = {}
    for (segment, sec_id), _inst in by_key.items():
        groups.setdefault(segment, []).append(int(sec_id))
    return groups


def _depth_price(levels: object) -> float | None:
    if isinstance(levels, list) and levels and isinstance(levels[0], dict):
        price = levels[0].get("price")
        if price:
            return float(price)
    return None


def quote_response_to_ticks(
    payload: dict,
    by_key: dict[tuple[str, str], DhanInstrument],
    *,
    sequences: dict[str, int],
    now: datetime,
) -> list[RawTick]:
    """Map a /v2/marketfeed/quote response into canonical RawTicks.

    ``sequences`` is a per-symbol monotonic counter owned by the caller (advanced in place),
    so ticks are strictly ordered across polling cycles. ``now`` is stamped as both the
    exchange and receive time: the caller only invokes this while the market is OPEN, so the
    prices are genuinely current — stale off-hours data is never presented as fresh.
    """
    ticks: list[RawTick] = []
    data = payload.get("data") or {}
    for segment, instruments in data.items():
        if not isinstance(instruments, dict):
            continue
        for sec_id, q in instruments.items():
            inst = by_key.get((segment, str(sec_id)))
            if inst is None or not isinstance(q, dict):
                continue
            ltp = float(q.get("last_price") or 0)
            if ltp <= 0:
                continue
            depth = q.get("depth") or {}
            seq = sequences.get(inst.symbol, 0) + 1
            sequences[inst.symbol] = seq
            ticks.append(
                RawTick(
                    symbol=inst.symbol,
                    exchange="NSE",
                    ltp=ltp,
                    ltq=int(q.get("last_quantity") or 0),
                    volume=int(q.get("volume") or 0),
                    sequence=seq,
                    exchange_ts=now,
                    bid=_depth_price(depth.get("buy")),
                    ask=_depth_price(depth.get("sell")),
                    received_ts=now,
                )
            )
    return ticks
