"""Tests for the pure DhanHQ mapping helpers (no network required)."""

from __future__ import annotations

from datetime import datetime, timezone

from market_intelligence.ingestion.dhan import (
    DhanSymbolSpec,
    quote_response_to_ticks,
    request_groups,
    resolve_security_ids,
)

# A tiny security-master sample in the compact column shape.
SAMPLE_CSV = (
    "SEM_EXM_EXCH_ID,SEM_SEGMENT,SEM_SMST_SECURITY_ID,SEM_TRADING_SYMBOL,SEM_CUSTOM_SYMBOL\n"
    "NSE,E,2885,RELIANCE,Reliance Industries\n"
    "NSE,E,11536,TCS,Tata Consultancy Services\n"
    "NSE,I,13,NIFTY,NIFTY 50\n"
    "NSE,I,25,BANKNIFTY,NIFTY BANK\n"
)

SPECS = (
    DhanSymbolSpec("RELIANCE", "NSE_EQ", ("RELIANCE",)),
    DhanSymbolSpec("TCS", "NSE_EQ", ("TCS",)),
    DhanSymbolSpec("NIFTY50", "IDX_I", ("NIFTY 50", "NIFTY")),
    DhanSymbolSpec("NIFTYBANK", "IDX_I", ("NIFTY BANK", "BANKNIFTY")),
    DhanSymbolSpec("MISSING", "NSE_EQ", ("NOTREAL",)),
)


def test_resolve_security_ids_matches_and_reports_unresolved():
    by_key, unresolved = resolve_security_ids(SAMPLE_CSV, SPECS)
    assert by_key[("NSE_EQ", "2885")].symbol == "RELIANCE"
    assert by_key[("NSE_EQ", "11536")].symbol == "TCS"
    assert by_key[("IDX_I", "13")].symbol == "NIFTY50"
    assert by_key[("IDX_I", "25")].symbol == "NIFTYBANK"
    assert unresolved == ["MISSING"]  # surfaced, not silently dropped


def test_request_groups_batches_by_segment():
    by_key, _ = resolve_security_ids(SAMPLE_CSV, SPECS)
    groups = request_groups(by_key)
    assert sorted(groups["NSE_EQ"]) == [2885, 11536]
    assert sorted(groups["IDX_I"]) == [13, 25]


def test_quote_response_to_ticks_maps_price_volume_and_orders():
    by_key, _ = resolve_security_ids(SAMPLE_CSV, SPECS)
    now = datetime(2026, 7, 20, 4, 0, tzinfo=timezone.utc)
    payload = {
        "status": "success",
        "data": {
            "NSE_EQ": {
                "2885": {
                    "last_price": 2954.5, "last_quantity": 10, "volume": 1200000,
                    "depth": {"buy": [{"price": 2954.4}], "sell": [{"price": 2954.6}]},
                },
            },
            "IDX_I": {
                "13": {"last_price": 24800.75, "volume": 0},  # index: no depth/qty
            },
        },
    }
    seqs: dict[str, int] = {}
    ticks = quote_response_to_ticks(payload, by_key, sequences=seqs, now=now)
    by_symbol = {t.symbol: t for t in ticks}

    r = by_symbol["RELIANCE"]
    assert r.ltp == 2954.5 and r.volume == 1200000 and r.ltq == 10
    assert r.bid == 2954.4 and r.ask == 2954.6
    assert r.exchange_ts == now and r.received_ts == now

    n = by_symbol["NIFTY50"]
    assert n.ltp == 24800.75 and n.bid is None and n.ask is None

    # Sequences advance per symbol across cycles.
    ticks2 = quote_response_to_ticks(payload, by_key, sequences=seqs, now=now)
    assert {t.symbol: t.sequence for t in ticks2}["RELIANCE"] == 2


def test_zero_or_missing_price_is_skipped():
    by_key, _ = resolve_security_ids(SAMPLE_CSV, SPECS)
    now = datetime(2026, 7, 20, 4, 0, tzinfo=timezone.utc)
    payload = {"data": {"NSE_EQ": {"2885": {"last_price": 0}}}}
    assert quote_response_to_ticks(payload, by_key, sequences={}, now=now) == []
