"""REST + WebSocket routes for the Event Fabric (SPEC-005 §6, §7).

Routes are thin: they translate HTTP/WS into calls on the injected fabric services and
back. All business-free — the fabric owns no domain logic (SPEC-005 §2).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, WebSocket, WebSocketDisconnect
from starlette import status

from nexus_shared.events.catalog import EventType
from nexus_shared.events.envelope import EventEnvelope
from event_fabric.api.dto import (
    HealthResponse,
    MetricsResponse,
    PublishRequest,
    PublishResponse,
    ReplayRequest,
    ReplayResponse,
    SchemaResponse,
)
from event_fabric.container import Container
from event_fabric.repositories.event_store import EventStoreRepository, ReplayQuery
from event_fabric.security import Principal, authenticate_ws_token, require_principal
from event_fabric.ws.gateway import CHANNELS

router = APIRouter(prefix="/events", tags=["event-fabric"])


def get_container(request: Request) -> Container:
    return request.app.state.container


@router.get("/health", response_model=HealthResponse)
async def health(container: Container = Depends(get_container)) -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=container.settings.service_name,
        environment=container.settings.environment,
    )


@router.get("/metrics", response_model=MetricsResponse)
async def metrics(container: Container = Depends(get_container)) -> MetricsResponse:
    async with container.database.session() as session:
        repo = EventStoreRepository(session)
        stored = await repo.count()
        dead = await repo.count_dead_letters()
    pub = container.publisher.metrics
    return MetricsResponse(
        events_stored=stored,
        dead_letters=dead,
        published=pub["published"],
        dead_lettered=pub["dead_lettered"],
        active_consumers=container.subscriptions.consumer_count,
        ws_connections=container.gateway.connection_count(),
        consumers=container.subscriptions.stats(),
    )


@router.post("", response_model=PublishResponse, status_code=status.HTTP_202_ACCEPTED)
async def publish(
    body: PublishRequest,
    container: Container = Depends(get_container),
    principal: Principal = Depends(require_principal),
) -> PublishResponse:
    """Publish an event. Producers use this REST ingress; the fabric never bypasses it."""
    fields = dict(
        event_type=body.event_type,
        event_version=body.event_version,
        producer=body.producer,
        aggregate_id=body.aggregate_id,
        payload=body.payload,
    )
    # Only set correlation_id when supplied; otherwise the envelope mints a fresh one.
    if body.correlation_id is not None:
        fields["correlation_id"] = body.correlation_id
    envelope = EventEnvelope(**fields)
    result = await container.publisher.publish(envelope)
    return PublishResponse(
        accepted=result.accepted,
        event_id=envelope.event_id if result.accepted else None,
        sequence=result.sequence,
        dead_letter_reason=result.dead_letter_reason,
    )


@router.post("/replay", response_model=ReplayResponse)
async def replay(
    body: ReplayRequest,
    container: Container = Depends(get_container),
    principal: Principal = Depends(require_principal),
) -> ReplayResponse:
    # Replay is available to any authenticated principal; it is read-only over the
    # immutable store and cannot corrupt state.
    report = await container.replay.replay(
        ReplayQuery(
            event_type=body.event_type,
            correlation_id=body.correlation_id,
            aggregate_id=body.aggregate_id,
            from_sequence=body.from_sequence,
            since=body.since,
            until=body.until,
            limit=body.limit,
        ),
        dispatch=body.dispatch,
    )
    return ReplayResponse(
        replayed=report.replayed,
        last_sequence=report.last_sequence,
        dispatched=report.dispatched,
    )


@router.get("/schema/{event}", response_model=SchemaResponse)
async def schema(
    event: EventType, container: Container = Depends(get_container)
) -> SchemaResponse:
    reg = container.registry
    versions = sorted(reg._schemas.get(event, {}).keys())  # noqa: SLF001 - read-only introspection
    return SchemaResponse(
        event_type=event,
        registered_versions=versions,
        latest_version=versions[-1] if versions else None,
    )


ws_router = APIRouter(tags=["event-fabric-ws"])


@ws_router.websocket("/ws/{channel}")
async def stream(websocket: WebSocket, channel: str) -> None:
    """Stream events for a channel (SPEC-005 §6). Auth via ``?token=`` query param."""
    container: Container = websocket.app.state.container
    if channel not in CHANNELS:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    try:
        authenticate_ws_token(websocket.query_params.get("token"), container.settings)
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await container.gateway.connect(channel, websocket)
    try:
        while True:
            # The stream is server-push; we await client frames only to detect disconnects
            # and honour heartbeats.
            await websocket.receive_text()
    except WebSocketDisconnect:
        await container.gateway.disconnect(channel, websocket)
