"""API contract tests over the FastAPI app (SPEC-005 §7)."""

from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from nexus_shared.events.catalog import EventType
from event_fabric.config import Settings
from event_fabric.main import create_app


@pytest_asyncio.fixture
async def client(registry):
    settings = Settings(
        EVENT_FABRIC_DATABASE_URL="sqlite+aiosqlite:///:memory:",
        auth_enabled=False,
        strict_schema_validation=True,
        event_signing_key="test-key",
    )
    app = create_app(settings, registry=registry)
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac


async def test_health(client: AsyncClient) -> None:
    resp = await client.get("/events/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


async def test_publish_and_metrics_roundtrip(client: AsyncClient) -> None:
    resp = await client.post(
        "/events",
        json={
            "event_type": EventType.TICK_RECEIVED.value,
            "producer": "market_intelligence",
            "aggregate_id": "RELIANCE",
            "payload": {"symbol": "RELIANCE", "ltp": 2950.0},
        },
    )
    assert resp.status_code == 202
    body = resp.json()
    assert body["accepted"] is True
    assert body["sequence"] == 1

    metrics = (await client.get("/events/metrics")).json()
    assert metrics["events_stored"] == 1
    assert metrics["published"] == 1


async def test_publish_invalid_payload_is_dead_lettered(client: AsyncClient) -> None:
    resp = await client.post(
        "/events",
        json={
            "event_type": EventType.TICK_RECEIVED.value,
            "producer": "market_intelligence",
            "payload": {"symbol": "RELIANCE"},
        },
    )
    assert resp.status_code == 202
    assert resp.json()["accepted"] is False
    assert resp.json()["dead_letter_reason"] == "invalid_schema"
    assert (await client.get("/events/metrics")).json()["dead_letters"] == 1


async def test_replay_endpoint(client: AsyncClient) -> None:
    for ltp in (1.0, 2.0):
        await client.post(
            "/events",
            json={
                "event_type": EventType.TICK_RECEIVED.value,
                "producer": "market_intelligence",
                "aggregate_id": "TCS",
                "payload": {"symbol": "TCS", "ltp": ltp},
            },
        )
    resp = await client.post("/events/replay", json={"aggregate_id": "TCS"})
    assert resp.status_code == 200
    assert resp.json()["replayed"] == 2


async def test_schema_endpoint(client: AsyncClient) -> None:
    resp = await client.get(f"/events/schema/{EventType.TICK_RECEIVED.value}")
    assert resp.status_code == 200
    assert resp.json()["registered_versions"] == [1]
    assert resp.json()["latest_version"] == 1
