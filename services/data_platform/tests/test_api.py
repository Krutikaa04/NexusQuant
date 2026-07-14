"""API contract tests over the FastAPI app (SPEC-006 §6, §7)."""

from __future__ import annotations

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from nexus_shared.events.catalog import EventType
from data_platform.config import Settings
from data_platform.main import create_app


@pytest_asyncio.fixture
async def client():
    settings = Settings(
        DATA_PLATFORM_DATABASE_URL="sqlite+aiosqlite:///:memory:", auth_enabled=False
    )
    app = create_app(settings)
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac


def dataset_body(name: str = "nifty_daily", content_hash: str = "hash_ds_api_1") -> dict:
    return {
        "event_type": EventType.DATASET_CREATED.value,
        "producer": "research_os",
        "payload": {
            "dataset_id": "ds-1",
            "name": name,
            "namespace": "market",
            "content_hash": content_hash,
            "storage_uri": "s3://x",
            "row_count": 10,
            "columns": ["a"],
        },
    }


async def test_health_reports_migrations(client) -> None:
    resp = await client.get("/data/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
    assert "0001_create_artifact_store" in resp.json()["migrations_applied"]


async def test_ingest_then_list_and_get(client) -> None:
    resp = await client.post("/data/ingest", json=dataset_body())
    assert resp.status_code == 202
    assert resp.json()["handled"] is True

    listed = await client.get("/datasets")
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    detail = await client.get("/datasets/market/nifty_daily")
    assert detail.status_code == 200
    assert detail.json()["latest_version"] == 1
    assert len(detail.json()["versions"]) == 1


async def test_get_missing_returns_404(client) -> None:
    resp = await client.get("/datasets/market/does_not_exist")
    assert resp.status_code == 404


async def test_ingest_malformed_payload_is_422(client) -> None:
    bad = dataset_body()
    del bad["payload"]["content_hash"]  # required field
    resp = await client.post("/data/ingest", json=bad)
    assert resp.status_code == 422
