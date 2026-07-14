"""REST routes for the Data Platform (SPEC-006 §6, §7).

Read endpoints (``/datasets``, ``/features``, ``/models``) serve the cached artifact views.
The ``/data/ingest`` endpoint is the consumer ingress: the fabric's subscriber delivers a
domain event here, which the indexing service processes. Routes stay thin — no SQL, no
business rules.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import ValidationError

from nexus_shared.events.envelope import EventEnvelope
from data_platform.api.dto import (
    HealthResponse,
    IngestRequest,
    IngestResponse,
)
from data_platform.container import Container
from data_platform.domain import ArtifactKind
from data_platform.security import Principal, require_principal

router = APIRouter(tags=["data-platform"])


def get_container(request: Request) -> Container:
    return request.app.state.container


@router.get("/data/health", response_model=HealthResponse)
async def health(container: Container = Depends(get_container)) -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=container.settings.service_name,
        environment=container.settings.environment,
        migrations_applied=container.applied_migrations,
    )


async def _list(container: Container, kind: ArtifactKind) -> list[dict]:
    return await container.queries.list_artifacts(kind)


async def _get(container: Container, kind: ArtifactKind, namespace: str, name: str) -> dict:
    view = await container.queries.get_artifact(kind, namespace, name)
    if view is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"{kind.value} not found")
    return view


@router.get("/datasets")
async def list_datasets(container: Container = Depends(get_container)) -> list[dict]:
    return await _list(container, ArtifactKind.DATASET)


@router.get("/datasets/{namespace}/{name}")
async def get_dataset(
    namespace: str, name: str, container: Container = Depends(get_container)
) -> dict:
    return await _get(container, ArtifactKind.DATASET, namespace, name)


@router.get("/features")
async def list_features(container: Container = Depends(get_container)) -> list[dict]:
    return await _list(container, ArtifactKind.FEATURE)


@router.get("/features/{namespace}/{name}")
async def get_feature(
    namespace: str, name: str, container: Container = Depends(get_container)
) -> dict:
    return await _get(container, ArtifactKind.FEATURE, namespace, name)


@router.get("/models")
async def list_models(container: Container = Depends(get_container)) -> list[dict]:
    return await _list(container, ArtifactKind.MODEL)


@router.get("/models/{namespace}/{name}")
async def get_model(
    namespace: str, name: str, container: Container = Depends(get_container)
) -> dict:
    return await _get(container, ArtifactKind.MODEL, namespace, name)


@router.post("/data/ingest", response_model=IngestResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest(
    body: IngestRequest,
    container: Container = Depends(get_container),
    principal: Principal = Depends(require_principal),
) -> IngestResponse:
    """Consumer ingress: process one domain event delivered from the fabric."""
    fields = dict(
        event_type=body.event_type,
        event_version=body.event_version,
        producer=body.producer,
        aggregate_id=body.aggregate_id,
        payload=body.payload,
    )
    if body.correlation_id is not None:
        fields["correlation_id"] = body.correlation_id
    try:
        result = await container.indexing.handle(EventEnvelope(**fields))
    except ValidationError as exc:
        # A malformed upstream payload is a bad request, not a server error.
        # Literal 422 avoids a Starlette constant rename across versions.
        raise HTTPException(422, detail=exc.errors()) from exc
    return IngestResponse(
        handled=result.handled,
        idempotent=result.idempotent,
        artifact_id=result.artifact_id,
        version_id=result.version_id,
        version=result.version,
    )
