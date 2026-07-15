"""API contract tests over the FastAPI app (SPEC-004 Public APIs)."""

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


RELIANCE = {
    "symbol": "RELIANCE",
    "name": "Reliance Industries",
    "segment": "EQ",
    "isin": "INE002A01018",
    "sector": "Energy",
}


async def test_health(client) -> None:
    resp = await client.get("/market/health")
    assert resp.status_code == 200
    assert "0001_create_market_schema" in resp.json()["migrations_applied"]


async def test_instrument_upsert_and_list(client) -> None:
    resp = await client.put("/market/instruments", json=RELIANCE)
    assert resp.status_code == 201
    assert resp.json()["revision"] == 1

    listed = await client.get("/market/instruments")
    assert listed.status_code == 200
    assert listed.json()[0]["symbol"] == "RELIANCE"

    # A second upsert versions the instrument.
    resp2 = await client.put("/market/instruments", json={**RELIANCE, "sector": "Conglomerate"})
    assert resp2.json()["revision"] == 2


async def test_mock_ingest_requires_registered_instruments(client) -> None:
    resp = await client.post(
        "/market/ingest/mock", json={"symbols": {"UNKNOWN": 100.0}, "count": 10}
    )
    assert resp.status_code == 422
    assert "UNKNOWN" in resp.json()["detail"]


async def test_ingest_then_query_roundtrip(client) -> None:
    await client.put("/market/instruments", json=RELIANCE)
    ingest = await client.post(
        "/market/ingest/mock", json={"symbols": {"RELIANCE": 2950.0}, "count": 150}
    )
    assert ingest.status_code == 202
    body = ingest.json()
    assert body["accepted"] == 150
    assert body["candles_closed"] >= 1

    ticks = await client.get("/market/ticks", params={"symbol": "RELIANCE", "limit": 10})
    assert ticks.status_code == 200
    assert len(ticks.json()) == 10

    candles = await client.get(
        "/market/candles", params={"symbol": "RELIANCE", "interval_seconds": 60}
    )
    assert candles.status_code == 200
    assert len(candles.json()) == body["candles_closed"]

    quality = await client.get("/market/quality", params={"symbol": "RELIANCE"})
    assert quality.status_code == 200
    assert quality.json()["readiness"] == "ready"


async def test_invalid_interval_rejected(client) -> None:
    resp = await client.get(
        "/market/candles", params={"symbol": "X", "interval_seconds": 42}
    )
    assert resp.status_code == 422


async def test_replay_endpoint(client) -> None:
    await client.put("/market/instruments", json=RELIANCE)
    await client.post(
        "/market/ingest/mock", json={"symbols": {"RELIANCE": 2950.0}, "count": 30}
    )
    resp = await client.post("/market/replay", params={"symbol": "RELIANCE", "limit": 100})
    assert resp.status_code == 200
    assert resp.json()["replayed"] == 30


async def test_quality_404_for_unknown_symbol(client) -> None:
    resp = await client.get("/market/quality", params={"symbol": "NOPE"})
    assert resp.status_code == 404
