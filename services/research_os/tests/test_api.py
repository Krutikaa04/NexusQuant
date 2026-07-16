"""API contract tests over the FastAPI app (SPEC-007 §6)."""

from __future__ import annotations

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from research_os.config import Settings
from research_os.main import create_app


@pytest_asyncio.fixture
async def client():
    settings = Settings(
        RESEARCH_DATABASE_URL="sqlite+aiosqlite:///:memory:", auth_enabled=False
    )
    app = create_app(settings)
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac


PROJECT = {
    "name": "Momentum Alpha",
    "owner": "asha",
    "description": "NIFTY momentum study",
    "tags": ["momentum"],
    "metadata": {"universe": "NIFTY50"},
}


async def create_project(client) -> str:
    resp = await client.post("/research/projects", json=PROJECT)
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def add_hypothesis(client, project_id: str) -> str:
    resp = await client.post(
        "/research/hypotheses",
        json={
            "project_id": project_id,
            "statement": "12-1 momentum predicts returns",
            "success_criteria": "IC > 0.05",
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def test_health(client) -> None:
    resp = await client.get("/research/health")
    assert resp.status_code == 200
    assert "0001_create_research_schema" in resp.json()["migrations_applied"]


async def test_project_crud_roundtrip(client) -> None:
    project_id = await create_project(client)

    listed = (await client.get("/research/projects")).json()
    assert len(listed) == 1 and listed[0]["status"] == "draft"
    assert listed[0]["allowed_transitions"] == ["active"]

    detail = (await client.get(f"/research/projects/{project_id}")).json()
    assert detail["metadata"] == {"universe": "NIFTY50"}

    patched = await client.patch(
        f"/research/projects/{project_id}", json={"tags": ["momentum", "v2"]}
    )
    assert patched.status_code == 200 and patched.json()["tags"] == ["momentum", "v2"]

    missing = await client.get("/research/projects/nope")
    assert missing.status_code == 404


async def test_validation_rejects_bad_input(client) -> None:
    resp = await client.post("/research/projects", json={"name": "ab", "owner": ""})
    assert resp.status_code == 422


async def test_transition_flow_and_illegal_rejection(client) -> None:
    project_id = await create_project(client)

    # Illegal skip (draft → experimenting) is rejected with 409.
    resp = await client.post(
        f"/research/projects/{project_id}/transition",
        json={"to_status": "experimenting", "actor": "asha"},
    )
    assert resp.status_code == 409

    # Activation without a hypothesis is a governance conflict.
    resp = await client.post(
        f"/research/projects/{project_id}/transition",
        json={"to_status": "active", "actor": "asha"},
    )
    assert resp.status_code == 409

    await add_hypothesis(client, project_id)
    resp = await client.post(
        f"/research/projects/{project_id}/transition",
        json={"to_status": "active", "actor": "asha"},
    )
    assert resp.status_code == 200 and resp.json()["status"] == "active"

    history = (await client.get(f"/research/projects/{project_id}/history")).json()
    assert [h["to_status"] for h in history] == ["draft", "active"]


async def test_experiment_endpoints(client) -> None:
    project_id = await create_project(client)
    await add_hypothesis(client, project_id)
    await client.post(
        f"/research/projects/{project_id}/transition",
        json={"to_status": "active", "actor": "asha"},
    )

    resp = await client.post(
        "/research/experiments",
        json={
            "project_id": project_id,
            "name": "baseline",
            "dataset_version": "nifty_daily@v3",
            "feature_version": "mom@v1",
        },
    )
    assert resp.status_code == 201
    exp_id = resp.json()["id"]

    started = await client.post(f"/research/experiments/{exp_id}/start")
    assert started.json()["status"] == "running"

    completed = await client.post(
        f"/research/experiments/{exp_id}/complete",
        json={"status": "completed", "metrics": {"sharpe": 1.2}},
    )
    assert completed.json()["metrics"] == {"sharpe": 1.2}

    # Double-complete is a conflict.
    again = await client.post(
        f"/research/experiments/{exp_id}/complete",
        json={"status": "failed", "metrics": {}},
    )
    assert again.status_code == 409


async def test_review_endpoints_and_dashboard(client) -> None:
    project_id = await create_project(client)
    resp = await client.post(
        "/research/reviews",
        json={
            "project_id": project_id,
            "reviewer": "vik",
            "decision": "needs_changes",
            "comments": "Add cost analysis.",
        },
    )
    assert resp.status_code == 201
    assert resp.json()["stage"] == "draft"

    reviews = (await client.get(f"/research/projects/{project_id}/reviews")).json()
    assert len(reviews) == 1

    dash = (await client.get("/research/dashboard")).json()
    assert dash["stats"]["projects"] == 1
    assert dash["stats"]["reviews"] == 1
    assert any(a["kind"] == "review" for a in dash["activity"])
    assert any(a["detail"] == "created" for a in dash["activity"])
