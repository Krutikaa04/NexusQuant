"""Query service — the cached read path (SPEC-006 §3, §10 performance targets).

Read-through cache: list/detail queries are served from the cache when warm and populated
from the repository on a miss. The indexing service invalidates the relevant kind-prefix on
every write, so reads are never stale beyond a single write.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from nexus_platform.cache.base import AbstractCache
from nexus_platform.db.session import Database
from data_platform import cache_keys
from data_platform.domain import ArtifactKind
from data_platform.repositories.artifacts import ArtifactRepository


@dataclass(frozen=True, slots=True)
class ArtifactView:
    artifact_id: str
    kind: str
    namespace: str
    name: str
    description: str | None
    owner_context: str
    latest_version: int | None
    version_count: int
    created_at: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class VersionView:
    version_id: str
    version: int
    content_hash: str
    status: str
    storage_uri: str | None
    payload: dict
    created_at: str


def _artifact_to_view(a) -> dict:
    versions = a.versions
    return asdict(
        ArtifactView(
            artifact_id=a.id,
            kind=a.kind,
            namespace=a.namespace,
            name=a.name,
            description=a.description,
            owner_context=a.owner_context,
            latest_version=max((v.version for v in versions), default=None),
            version_count=len(versions),
            created_at=a.created_at.isoformat(),
            updated_at=a.updated_at.isoformat(),
        )
    )


class QueryService:
    def __init__(self, database: Database, cache: AbstractCache, *, ttl: int = 300) -> None:
        self._db = database
        self._cache = cache
        self._ttl = ttl

    async def list_artifacts(self, kind: ArtifactKind) -> list[dict]:
        cache_key = cache_keys.list_key(kind)
        cached = await self._cache.get_json(cache_key)
        if cached is not None:
            return cached
        async with self._db.session() as session:
            artifacts = await ArtifactRepository(session).list_by_kind(kind)
            views = [_artifact_to_view(a) for a in artifacts]
        await self._cache.set_json(cache_key, views, ttl=self._ttl)
        return views

    async def get_artifact(
        self, kind: ArtifactKind, namespace: str, name: str
    ) -> dict | None:
        cache_key = cache_keys.item_key(kind, namespace, name)
        cached = await self._cache.get_json(cache_key)
        if cached is not None:
            return cached
        async with self._db.session() as session:
            artifact = await ArtifactRepository(session).get_by_identity(kind, namespace, name)
            if artifact is None:
                return None
            view = _artifact_to_view(artifact)
            view["versions"] = [
                asdict(
                    VersionView(
                        version_id=v.id,
                        version=v.version,
                        content_hash=v.content_hash,
                        status=v.status,
                        storage_uri=v.storage_uri,
                        payload=v.payload,
                        created_at=v.created_at.isoformat(),
                    )
                )
                for v in artifact.versions
            ]
        await self._cache.set_json(cache_key, view, ttl=self._ttl)
        return view
