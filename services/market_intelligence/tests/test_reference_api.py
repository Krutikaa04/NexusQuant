"""API tests for calendar, corporate actions, and adjusted candles (SPEC-004)."""

from __future__ import annotations

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from market_intelligence.config import Settings
from market_intelligence.main import create_app


@pytest_asyncio.fixture
async def client():
    settings = Settings(MARKET_DATABASE_URL="sqlite+aiosqlite:///:memory:", auth_enabled=False)
    app = create_app(settings)
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac


async def test_calendar_endpoint_with_holiday(client) -> None:
    resp = await client.put(
        "/market/calendar/holidays", json={"day": "2024-01-26", "reason": "Republic Day"}
    )
    assert resp.status_code == 201

    info = (await client.get("/market/calendar", params={"day": "2024-01-26"})).json()
    assert info["is_holiday"] is True
    assert info["is_trading_day"] is False
    assert info["session_open"] is None

    monday = (await client.get("/market/calendar", params={"day": "2024-01-22"})).json()
    assert monday["is_trading_day"] is True
    assert monday["session_open"] == "09:15:00"
    assert monday["weekly_expiry"] == "2024-01-25"


async def test_corporate_action_and_adjusted_candles(client) -> None:
    # Seed instrument + ticks so candles exist.
    await client.put(
        "/market/instruments", json={"symbol": "IRCTC", "name": "IRCTC Ltd", "segment": "EQ"}
    )
    ingest = await client.post(
        "/market/ingest/mock", json={"symbols": {"IRCTC": 1000.0}, "count": 120}
    )
    assert ingest.json()["candles_closed"] >= 1

    # Record a 1:10 split with ex-date after the mock data (2024-01-01).
    resp = await client.post(
        "/market/corporate-actions",
        json={
            "symbol": "IRCTC",
            "action_type": "split",
            "ex_date": "2024-06-01",
            "details": {"ratio_from": 1, "ratio_to": 10},
        },
    )
    assert resp.status_code == 201
    assert resp.json()["adjustment_version"] == 1

    listed = (await client.get(
        "/market/corporate-actions", params={"symbol": "IRCTC"}
    )).json()
    assert len(listed) == 1

    raw = (await client.get("/market/candles", params={"symbol": "IRCTC"})).json()
    adjusted = (await client.get(
        "/market/candles/adjusted", params={"symbol": "IRCTC"}
    )).json()
    assert len(adjusted) == len(raw)
    # Candles predate the ex-date, so adjusted = raw * 0.1.
    assert abs(adjusted[0]["close"] - raw[0]["close"] * 0.1) < 1e-6
    assert adjusted[0]["adjustment_factor"] == 0.1

    # Version pinning: as of version 0 (no actions), prices are unadjusted.
    pinned = (await client.get(
        "/market/candles/adjusted", params={"symbol": "IRCTC", "up_to_version": 0}
    )).json()
    assert pinned[0]["close"] == raw[0]["close"]


async def test_regime_endpoints(client) -> None:
    resp = await client.get("/market/regime", params={"symbol": "NOPE"})
    assert resp.status_code == 404

    await client.put(
        "/market/instruments", json={"symbol": "TCS", "name": "TCS Ltd", "segment": "EQ"}
    )
    await client.post(
        "/market/ingest/mock", json={"symbols": {"TCS": 3900.0}, "count": 2400}
    )
    assessed = await client.post("/market/regime/assess", params={"symbol": "TCS"})
    assert assessed.status_code == 200
    body = assessed.json()
    assert body["regimes"]

    current = (await client.get("/market/regime", params={"symbol": "TCS"})).json()
    assert current["regimes"] == body["regimes"]


async def test_regime_assess_insufficient_history(client) -> None:
    await client.put(
        "/market/instruments", json={"symbol": "INFY", "name": "Infosys", "segment": "EQ"}
    )
    resp = await client.post("/market/regime/assess", params={"symbol": "INFY"})
    assert resp.status_code == 422
