"""API tests driving the FastAPI app end-to-end over ASGI."""

from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from strategy_core.config import Settings
from strategy_core.main import create_app


@pytest_asyncio.fixture
async def client():
    settings = Settings(STRATEGY_DATABASE_URL="sqlite+aiosqlite:///:memory:", auth_enabled=False)
    app = create_app(settings)
    transport = ASGITransport(app=app)
    async with app.router.lifespan_context(app):
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            yield c


def _payload(name="API Strategy"):
    return {
        "name": name,
        "description": "created via api",
        "category": "momentum",
        "owner": "api@nexus",
        "tags": ["api"],
        "config": {"symbols": ["SBIN"], "exchanges": ["NSE"], "timeframes": ["1m"]},
    }


async def test_health(client):
    r = await client.get("/strategies/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


async def test_create_and_get(client):
    r = await client.post("/strategies", json=_payload())
    assert r.status_code == 201
    sid = r.json()["id"]
    got = await client.get(f"/strategies/{sid}")
    assert got.status_code == 200
    assert got.json()["configuration"]["symbols"] == ["SBIN"]


async def test_list_and_summary(client):
    await client.post("/strategies", json=_payload("One"))
    await client.post("/strategies", json=_payload("Two"))
    listing = await client.get("/strategies")
    assert listing.status_code == 200
    assert len(listing.json()) == 2
    summary = await client.get("/strategies/summary")
    assert summary.status_code == 200
    assert summary.json()["total"] == 2


async def test_transition_and_illegal(client):
    sid = (await client.post("/strategies", json=_payload())).json()["id"]
    ok = await client.post(f"/strategies/{sid}/transition", json={"to_status": "configured"})
    assert ok.status_code == 200
    assert ok.json()["status"] == "configured"
    bad = await client.post(f"/strategies/{sid}/transition", json={"to_status": "ready"})
    assert bad.status_code == 409


async def test_archive_endpoint(client):
    sid = (await client.post("/strategies", json=_payload())).json()["id"]
    r = await client.post(f"/strategies/{sid}/archive")
    assert r.status_code == 200
    assert r.json()["status"] == "archived"


async def test_update_versions_and_rollback(client):
    sid = (await client.post("/strategies", json=_payload())).json()["id"]
    upd = await client.patch(f"/strategies/{sid}", json={"name": "Renamed"})
    assert upd.status_code == 200
    assert upd.json()["version"] == 2
    versions = await client.get(f"/strategies/{sid}/versions")
    assert len(versions.json()) == 2
    rolled = await client.post(f"/strategies/{sid}/rollback", json={"version": 1})
    assert rolled.status_code == 200
    assert rolled.json()["name"] == "API Strategy"


async def test_clone_and_audit(client):
    sid = (await client.post("/strategies", json=_payload())).json()["id"]
    clone = await client.post(f"/strategies/{sid}/clone", json={"name": "Cloned"})
    assert clone.status_code == 201
    assert clone.json()["id"] != sid
    audit = await client.get(f"/strategies/{sid}/audit")
    assert audit.status_code == 200
    assert any(a["action"] == "created" for a in audit.json())


async def test_delete_then_404(client):
    sid = (await client.post("/strategies", json=_payload())).json()["id"]
    d = await client.delete(f"/strategies/{sid}")
    assert d.status_code == 204
    assert (await client.get(f"/strategies/{sid}")).status_code == 404


async def test_validation_rejects_bad_body(client):
    r = await client.post("/strategies", json={"name": ""})
    assert r.status_code == 422  # pydantic min_length
