"""Indexing service tests: event-sourced writes, idempotency, lineage, outbound events."""

from __future__ import annotations

from nexus_shared.events.catalog import EventType
from nexus_shared.events.envelope import EventEnvelope
from data_platform.domain import ArtifactKind
from data_platform.repositories.artifacts import ArtifactRepository


async def test_dataset_created_indexes_and_publishes(container, publisher, dataset_event) -> None:
    result = await container.indexing.handle(dataset_event())
    assert result.handled and not result.idempotent
    assert result.version == 1

    async with container.database.session() as session:
        artifact = await ArtifactRepository(session).get_by_identity(
            ArtifactKind.DATASET, "market", "nifty_daily"
        )
    assert artifact is not None
    assert len(artifact.versions) == 1

    # Publishes DatasetIndexed and ReadModelUpdated, correlated to the source event.
    types = [e.event_type for e in publisher.published]
    assert EventType.DATASET_INDEXED in types
    assert EventType.READ_MODEL_UPDATED in types


async def test_dataset_created_is_idempotent(container, publisher, dataset_event) -> None:
    event = dataset_event()
    await container.indexing.handle(event)
    published_after_first = len(publisher.published)
    result = await container.indexing.handle(event)  # redelivery, same content_hash
    assert result.idempotent
    assert len(publisher.published) == published_after_first  # no duplicate outbound events


async def test_feature_version_records_lineage(container, dataset_event) -> None:
    # Seed a dataset version to link from.
    ds = await container.indexing.handle(dataset_event())
    feature = EventEnvelope(
        event_type=EventType.FEATURE_VERSION_CREATED,
        producer="alpha_factory",
        payload={
            "feature_id": "f-1",
            "name": "rsi_14",
            "namespace": "momentum",
            "version": 1,
            "content_hash": "hash_feat_0001",
            "definition": {"window": 14},
            "upstream_dataset_version_id": ds.version_id,
        },
    )
    result = await container.indexing.handle(feature)
    assert result.handled

    from data_platform.repositories.lineage import LineageRepository

    async with container.database.session() as session:
        edges = await LineageRepository(session).downstream_of(ds.version_id)
    assert len(edges) == 1
    assert edges[0].relation == "engineered_from"


async def test_model_validated_indexes_with_metrics(container) -> None:
    event = EventEnvelope(
        event_type=EventType.MODEL_VALIDATED,
        producer="alpha_factory",
        payload={
            "model_id": "m-1",
            "name": "xgb_reversal",
            "namespace": "mean_reversion",
            "version": 3,
            "content_hash": "hash_model_0003",
            "metrics": {"sharpe": 1.8, "hit_rate": 0.56},
        },
    )
    result = await container.indexing.handle(event)
    assert result.handled and result.version == 3

    async with container.database.session() as session:
        artifact = await ArtifactRepository(session).get_by_identity(
            ArtifactKind.MODEL, "mean_reversion", "xgb_reversal"
        )
    assert artifact.versions[0].payload["metrics"]["sharpe"] == 1.8


async def test_unknown_event_is_ignored(container) -> None:
    event = EventEnvelope(
        event_type=EventType.ORDER_FILLED, producer="execution", payload={}
    )
    result = await container.indexing.handle(event)
    assert not result.handled
