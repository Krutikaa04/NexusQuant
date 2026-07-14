"""Repository tests: immutable versioning, idempotency, lineage, read models (SPEC-006 §5)."""

from __future__ import annotations

from data_platform.domain import ArtifactKind, ArtifactStatus
from data_platform.repositories.artifacts import ArtifactRepository
from data_platform.repositories.lineage import LineageRepository
from data_platform.repositories.read_models import ReadModelRepository


async def test_append_version_increments(container) -> None:
    async with container.database.begin() as session:
        repo = ArtifactRepository(session)
        artifact = await repo.get_or_create(
            kind=ArtifactKind.DATASET, namespace="market", name="ds", owner_context="research_os"
        )
        v1 = await repo.append_version(
            artifact, content_hash="h1", status=ArtifactStatus.INDEXED, payload={}
        )
        v2 = await repo.append_version(
            artifact, content_hash="h2", status=ArtifactStatus.INDEXED, payload={}
        )
    assert (v1.version, v2.version) == (1, 2)


async def test_append_version_idempotent_by_hash(container) -> None:
    async with container.database.begin() as session:
        repo = ArtifactRepository(session)
        artifact = await repo.get_or_create(
            kind=ArtifactKind.DATASET, namespace="market", name="ds", owner_context="research_os"
        )
        first = await repo.append_version(
            artifact, content_hash="same", status=ArtifactStatus.INDEXED, payload={}
        )
        second = await repo.append_version(
            artifact, content_hash="same", status=ArtifactStatus.INDEXED, payload={}
        )
    assert first.id == second.id  # no duplicate version created


async def test_get_or_create_is_stable(container) -> None:
    async with container.database.begin() as session:
        repo = ArtifactRepository(session)
        a = await repo.get_or_create(
            kind=ArtifactKind.FEATURE, namespace="ns", name="rsi", owner_context="alpha"
        )
        b = await repo.get_or_create(
            kind=ArtifactKind.FEATURE, namespace="ns", name="rsi", owner_context="alpha"
        )
    assert a.id == b.id


async def test_lineage_edges(container) -> None:
    async with container.database.begin() as session:
        lineage = LineageRepository(session)
        await lineage.add_edge("v-up", "v-down", relation="engineered_from")
    async with container.database.session() as session:
        edges = await LineageRepository(session).upstream_of("v-down")
    assert len(edges) == 1
    assert edges[0].upstream_version_id == "v-up"


async def test_read_model_revision_bumps(container) -> None:
    async with container.database.begin() as session:
        repo = ReadModelRepository(session)
        await repo.upsert("k", "dataset", {"v": 1})
        await repo.upsert("k", "dataset", {"v": 2})
    async with container.database.session() as session:
        rm = await ReadModelRepository(session).get("k")
    assert rm.revision == 2
    assert rm.projection == {"v": 2}
