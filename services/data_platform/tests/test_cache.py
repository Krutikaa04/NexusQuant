"""Cache-invalidation tests for the query path (SPEC-006 §10, cache invalidation)."""

from __future__ import annotations

from data_platform.domain import ArtifactKind


async def test_list_reflects_writes_after_invalidation(container, dataset_event) -> None:
    # Warm the cache with an empty list.
    assert await container.queries.list_artifacts(ArtifactKind.DATASET) == []
    # Write via the indexing path (which invalidates the dataset cache prefix).
    await container.indexing.handle(dataset_event())
    # The next read must recompute and include the new dataset.
    listed = await container.queries.list_artifacts(ArtifactKind.DATASET)
    assert len(listed) == 1
    assert listed[0]["name"] == "nifty_daily"


async def test_detail_is_cached_and_served(container, dataset_event) -> None:
    await container.indexing.handle(dataset_event())
    first = await container.queries.get_artifact(ArtifactKind.DATASET, "market", "nifty_daily")
    second = await container.queries.get_artifact(ArtifactKind.DATASET, "market", "nifty_daily")
    assert first == second
    assert first["version_count"] == 1
    assert first["versions"][0]["status"] == "indexed"


async def test_missing_artifact_returns_none(container) -> None:
    assert await container.queries.get_artifact(ArtifactKind.MODEL, "x", "y") is None
