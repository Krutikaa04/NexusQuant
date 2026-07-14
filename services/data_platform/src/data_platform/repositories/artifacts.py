"""Repository over artifacts and their immutable versions (SPEC-006 §5, §15).

Enforces the append-only invariant at the boundary: :meth:`append_version` computes the
next version number for an artifact and refuses to mutate any existing version. Callers
never issue SQL; they add versions and query by identity.
"""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from nexus_platform.db.repository import BaseRepository
from nexus_shared.primitives.time import utc_now
from data_platform.db.models import Artifact, ArtifactVersion
from data_platform.domain import ArtifactKind, ArtifactStatus


class DuplicateContentError(RuntimeError):
    """Raised when a version with an identical content hash already exists (idempotency)."""


class ArtifactRepository(BaseRepository[Artifact]):
    model = Artifact

    async def get_by_identity(
        self, kind: ArtifactKind, namespace: str, name: str
    ) -> Artifact | None:
        stmt = (
            select(Artifact)
            .where(
                Artifact.kind == kind.value,
                Artifact.namespace == namespace,
                Artifact.name == name,
            )
            .options(selectinload(Artifact.versions))
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_or_create(
        self,
        *,
        kind: ArtifactKind,
        namespace: str,
        name: str,
        owner_context: str,
        description: str | None = None,
    ) -> Artifact:
        existing = await self.get_by_identity(kind, namespace, name)
        if existing is not None:
            return existing
        now = utc_now()
        artifact = Artifact(
            id=str(uuid4()),
            kind=kind.value,
            namespace=namespace,
            name=name,
            description=description,
            owner_context=owner_context,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        return await self.add(artifact)

    async def _next_version(self, artifact_id: str) -> int:
        stmt = select(func.max(ArtifactVersion.version)).where(
            ArtifactVersion.artifact_id == artifact_id
        )
        current = (await self.session.execute(stmt)).scalar_one_or_none()
        return (current or 0) + 1

    async def find_version_by_hash(self, content_hash: str) -> ArtifactVersion | None:
        stmt = select(ArtifactVersion).where(ArtifactVersion.content_hash == content_hash)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def append_version(
        self,
        artifact: Artifact,
        *,
        content_hash: str,
        status: ArtifactStatus,
        payload: dict,
        storage_uri: str | None = None,
        source_event_id: str | None = None,
        explicit_version: int | None = None,
    ) -> ArtifactVersion:
        """Append a new immutable version. Idempotent by ``content_hash``.

        Re-delivery of the same source event (identical content hash) returns the existing
        version rather than creating a duplicate — this makes consumers idempotent as the
        event fabric requires (SPEC-005 §5).
        """
        existing = await self.find_version_by_hash(content_hash)
        if existing is not None:
            return existing

        version = explicit_version or await self._next_version(artifact.id)
        record = ArtifactVersion(
            id=str(uuid4()),
            artifact_id=artifact.id,
            version=version,
            content_hash=content_hash,
            storage_uri=storage_uri,
            status=status.value,
            payload=payload,
            source_event_id=source_event_id,
            created_at=utc_now(),
        )
        self.session.add(record)
        artifact.updated_at = utc_now()
        await self.session.flush()
        return record

    async def list_by_kind(
        self, kind: ArtifactKind, *, include_inactive: bool = False
    ) -> list[Artifact]:
        stmt = (
            select(Artifact)
            .where(Artifact.kind == kind.value)
            .options(selectinload(Artifact.versions))
            .order_by(Artifact.created_at.desc())
        )
        if not include_inactive:
            stmt = stmt.where(Artifact.is_active.is_(True))
        return list((await self.session.execute(stmt)).scalars().all())

    async def get_versions(self, artifact_id: str) -> list[ArtifactVersion]:
        stmt = (
            select(ArtifactVersion)
            .where(ArtifactVersion.artifact_id == artifact_id)
            .order_by(ArtifactVersion.version.asc())
        )
        return list((await self.session.execute(stmt)).scalars().all())
