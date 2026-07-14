"""Indexing service — the event-sourced write path (SPEC-006 §7).

Consumes the immutable-artifact events (``DatasetCreated``, ``FeatureVersionCreated``,
``ModelValidated``), materialises the corresponding artifact version, records lineage,
refreshes the read model, and publishes ``DatasetIndexed`` / ``ReadModelUpdated`` back onto
the fabric. Every handler is **idempotent** by content hash (SPEC-005 §5): a re-delivered
event is recognised and produces no duplicate state or duplicate outbound events.

All persistence for one event happens in a single transaction; outbound events are
published only after that transaction commits, so the fabric never advertises state that
did not durably land.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from nexus_shared.events.catalog import EventType
from nexus_shared.events.envelope import EventEnvelope
from nexus_platform.cache.base import AbstractCache
from nexus_platform.db.session import Database
from data_platform import cache_keys
from data_platform.domain import ArtifactKind, ArtifactStatus
from data_platform.events.publisher import EventPublisher
from data_platform.events.schemas import (
    DatasetCreatedPayload,
    FeatureVersionCreatedPayload,
    ModelValidatedPayload,
)
from data_platform.repositories.artifacts import ArtifactRepository
from data_platform.repositories.lineage import LineageRepository
from data_platform.repositories.read_models import ReadModelRepository

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class IndexResult:
    handled: bool
    idempotent: bool = False
    artifact_id: str | None = None
    version_id: str | None = None
    version: int | None = None


class IndexingService:
    def __init__(
        self, database: Database, publisher: EventPublisher, cache: AbstractCache
    ) -> None:
        self._db = database
        self._publisher = publisher
        self._cache = cache

    async def handle(self, envelope: EventEnvelope) -> IndexResult:
        """Route an inbound event to its handler. Unknown types are ignored (not this
        context's concern), matching a real subscriber that filters by interest."""
        match envelope.event_type:
            case EventType.DATASET_CREATED:
                return await self._handle_dataset_created(envelope)
            case EventType.FEATURE_VERSION_CREATED:
                return await self._handle_feature_version(envelope)
            case EventType.MODEL_VALIDATED:
                return await self._handle_model_validated(envelope)
            case _:
                return IndexResult(handled=False)

    async def _handle_dataset_created(self, envelope: EventEnvelope) -> IndexResult:
        p = DatasetCreatedPayload.model_validate(envelope.payload)
        outbound: list[EventEnvelope] = []
        async with self._db.begin() as session:
            repo = ArtifactRepository(session)
            if await repo.find_version_by_hash(p.content_hash) is not None:
                return IndexResult(handled=True, idempotent=True)
            artifact = await repo.get_or_create(
                kind=ArtifactKind.DATASET,
                namespace=p.namespace,
                name=p.name,
                owner_context=envelope.producer,
                description=p.description,
            )
            version = await repo.append_version(
                artifact,
                content_hash=p.content_hash,
                status=ArtifactStatus.INDEXED,
                payload={"row_count": p.row_count, "columns": p.columns, "dataset_id": p.dataset_id},
                storage_uri=p.storage_uri,
                source_event_id=str(envelope.event_id),
            )
            rm_key = await self._refresh_read_model(
                session, ArtifactKind.DATASET, artifact, version
            )
            outbound.append(
                self._event(
                    envelope,
                    EventType.DATASET_INDEXED,
                    {
                        "artifact_id": artifact.id,
                        "version_id": version.id,
                        "name": artifact.name,
                        "namespace": artifact.namespace,
                        "version": version.version,
                        "content_hash": version.content_hash,
                    },
                    aggregate_id=artifact.id,
                )
            )
            outbound.append(self._read_model_event(envelope, rm_key, ArtifactKind.DATASET))
            result = IndexResult(
                handled=True,
                artifact_id=artifact.id,
                version_id=version.id,
                version=version.version,
            )
        await self._invalidate(ArtifactKind.DATASET)
        await self._publish_all(outbound)
        return result

    async def _handle_feature_version(self, envelope: EventEnvelope) -> IndexResult:
        p = FeatureVersionCreatedPayload.model_validate(envelope.payload)
        outbound: list[EventEnvelope] = []
        async with self._db.begin() as session:
            repo = ArtifactRepository(session)
            if await repo.find_version_by_hash(p.content_hash) is not None:
                return IndexResult(handled=True, idempotent=True)
            artifact = await repo.get_or_create(
                kind=ArtifactKind.FEATURE,
                namespace=p.namespace,
                name=p.name,
                owner_context=envelope.producer,
            )
            version = await repo.append_version(
                artifact,
                content_hash=p.content_hash,
                status=ArtifactStatus.VALIDATED,
                payload={"definition": p.definition, "feature_id": p.feature_id},
                source_event_id=str(envelope.event_id),
                explicit_version=p.version,
            )
            if p.upstream_dataset_version_id:
                await LineageRepository(session).add_edge(
                    p.upstream_dataset_version_id, version.id, relation="engineered_from"
                )
            rm_key = await self._refresh_read_model(
                session, ArtifactKind.FEATURE, artifact, version
            )
            outbound.append(self._read_model_event(envelope, rm_key, ArtifactKind.FEATURE))
            result = IndexResult(
                handled=True, artifact_id=artifact.id, version_id=version.id, version=version.version
            )
        await self._invalidate(ArtifactKind.FEATURE)
        await self._publish_all(outbound)
        return result

    async def _handle_model_validated(self, envelope: EventEnvelope) -> IndexResult:
        p = ModelValidatedPayload.model_validate(envelope.payload)
        outbound: list[EventEnvelope] = []
        async with self._db.begin() as session:
            repo = ArtifactRepository(session)
            if await repo.find_version_by_hash(p.content_hash) is not None:
                return IndexResult(handled=True, idempotent=True)
            artifact = await repo.get_or_create(
                kind=ArtifactKind.MODEL,
                namespace=p.namespace,
                name=p.name,
                owner_context=envelope.producer,
            )
            version = await repo.append_version(
                artifact,
                content_hash=p.content_hash,
                status=ArtifactStatus.VALIDATED,
                payload={"metrics": p.metrics, "model_id": p.model_id},
                storage_uri=p.storage_uri,
                source_event_id=str(envelope.event_id),
                explicit_version=p.version,
            )
            lineage = LineageRepository(session)
            for upstream in p.upstream_feature_version_ids:
                await lineage.add_edge(upstream, version.id, relation="trained_on")
            rm_key = await self._refresh_read_model(session, ArtifactKind.MODEL, artifact, version)
            outbound.append(self._read_model_event(envelope, rm_key, ArtifactKind.MODEL))
            result = IndexResult(
                handled=True, artifact_id=artifact.id, version_id=version.id, version=version.version
            )
        await self._invalidate(ArtifactKind.MODEL)
        await self._publish_all(outbound)
        return result

    # --- helpers ---

    async def _refresh_read_model(self, session, kind, artifact, version) -> str:
        key = cache_keys.read_model_key(kind, artifact.namespace, artifact.name)
        projection = {
            "artifact_id": artifact.id,
            "kind": kind.value,
            "namespace": artifact.namespace,
            "name": artifact.name,
            "latest_version": version.version,
            "content_hash": version.content_hash,
            "status": version.status,
            "updated_at": artifact.updated_at.isoformat(),
        }
        await ReadModelRepository(session).upsert(key, kind.value, projection)
        return key

    def _event(self, source, event_type, payload, *, aggregate_id=None) -> EventEnvelope:
        return EventEnvelope(
            event_type=event_type,
            producer="data_platform",
            correlation_id=source.correlation_id,
            aggregate_id=aggregate_id,
            payload=payload,
        )

    def _read_model_event(self, source, key: str, kind: ArtifactKind) -> EventEnvelope:
        return self._event(
            source,
            EventType.READ_MODEL_UPDATED,
            {"key": key, "kind": kind.value},
            aggregate_id=key,
        )

    async def _invalidate(self, kind: ArtifactKind) -> None:
        await self._cache.clear_prefix(cache_keys.kind_prefix(kind))

    async def _publish_all(self, events: list[EventEnvelope]) -> None:
        for event in events:
            await self._publisher.publish(event)
