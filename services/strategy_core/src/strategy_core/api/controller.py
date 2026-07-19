"""REST routes for Strategy Core. Thin controllers — all logic lives in the service layer."""

from __future__ import annotations

from contextlib import contextmanager

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from starlette import status as http

from strategy_core.api.dto import (
    CloneBody,
    CreateStrategyBody,
    HealthResponse,
    RollbackBody,
    TransitionBody,
    UpdateStrategyBody,
)
from strategy_core.container import Container
from strategy_core.domain.errors import (
    IllegalTransition,
    ImmutableStrategy,
    StrategyNotFound,
    ValidationError,
)
from strategy_core.security import Principal, require_principal

router = APIRouter(prefix="/strategies", tags=["strategy-core"])


def get_container(request: Request) -> Container:
    # Standalone app stores the strategy container as ``container``; a composing BFF (which
    # already owns ``container`` for another context) stores it as ``strategy_container``.
    state = request.app.state
    return getattr(state, "strategy_container", None) or state.container


@contextmanager
def _translate():
    """Map domain errors to HTTP status codes at the edge."""
    try:
        yield
    except StrategyNotFound as exc:
        raise HTTPException(http.HTTP_404_NOT_FOUND, detail=str(exc) or "not found")
    except IllegalTransition as exc:
        raise HTTPException(http.HTTP_409_CONFLICT, detail=str(exc))
    except ImmutableStrategy as exc:
        raise HTTPException(http.HTTP_409_CONFLICT, detail=str(exc))
    except ValidationError as exc:
        raise HTTPException(http.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/health", response_model=HealthResponse)
async def health(container: Container = Depends(get_container)) -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=container.settings.service_name,
        environment=container.settings.environment,
        migrations_applied=container.applied_migrations,
    )


@router.get("/summary")
async def dashboard_summary(container: Container = Depends(get_container)) -> dict:
    return await container.dashboard.summary()


@router.get("")
async def list_strategies(
    status: str | None = None,
    category: str | None = None,
    owner: str | None = None,
    tag: str | None = None,
    container: Container = Depends(get_container),
) -> list[dict]:
    return await container.strategies.list_strategies(
        status=status, category=category, owner=owner, tag=tag
    )


@router.post("", status_code=http.HTTP_201_CREATED)
async def create_strategy(
    body: CreateStrategyBody,
    container: Container = Depends(get_container),
    principal: Principal = Depends(require_principal),
) -> dict:
    with _translate():
        return await container.strategies.create_strategy(
            name=body.name, description=body.description, category=body.category,
            owner=body.owner, tags=body.tags, config=body.config, actor=principal.subject,
        )


@router.get("/{strategy_id}")
async def get_strategy(
    strategy_id: str, container: Container = Depends(get_container)
) -> dict:
    with _translate():
        return await container.strategies.get_detail(strategy_id)


@router.patch("/{strategy_id}")
async def update_strategy(
    strategy_id: str,
    body: UpdateStrategyBody,
    container: Container = Depends(get_container),
    principal: Principal = Depends(require_principal),
) -> dict:
    with _translate():
        return await container.strategies.update_strategy(
            strategy_id, name=body.name, description=body.description,
            category=body.category, tags=body.tags, config=body.config,
            change_summary=body.change_summary, actor=principal.subject,
        )


@router.delete("/{strategy_id}", status_code=http.HTTP_204_NO_CONTENT)
async def delete_strategy(
    strategy_id: str,
    container: Container = Depends(get_container),
    principal: Principal = Depends(require_principal),
) -> Response:
    with _translate():
        await container.strategies.soft_delete(strategy_id, actor=principal.subject)
    return Response(status_code=http.HTTP_204_NO_CONTENT)


@router.post("/{strategy_id}/transition")
async def transition_strategy(
    strategy_id: str,
    body: TransitionBody,
    container: Container = Depends(get_container),
    principal: Principal = Depends(require_principal),
) -> dict:
    with _translate():
        return await container.strategies.transition(
            strategy_id, to_status=body.to_status, reason=body.reason,
            actor=principal.subject,
        )


@router.post("/{strategy_id}/archive")
async def archive_strategy(
    strategy_id: str,
    container: Container = Depends(get_container),
    principal: Principal = Depends(require_principal),
) -> dict:
    with _translate():
        return await container.strategies.archive(strategy_id, actor=principal.subject)


@router.post("/{strategy_id}/rollback")
async def rollback_strategy(
    strategy_id: str,
    body: RollbackBody,
    container: Container = Depends(get_container),
    principal: Principal = Depends(require_principal),
) -> dict:
    with _translate():
        return await container.strategies.rollback(
            strategy_id, to_version=body.version, actor=principal.subject
        )


@router.post("/{strategy_id}/clone", status_code=http.HTTP_201_CREATED)
async def clone_strategy(
    strategy_id: str,
    body: CloneBody,
    container: Container = Depends(get_container),
    principal: Principal = Depends(require_principal),
) -> dict:
    with _translate():
        return await container.strategies.clone_strategy(
            strategy_id, new_name=body.name, actor=principal.subject
        )


@router.get("/{strategy_id}/versions")
async def list_versions(
    strategy_id: str, container: Container = Depends(get_container)
) -> list[dict]:
    with _translate():
        return await container.strategies.list_versions(strategy_id)


@router.get("/{strategy_id}/compare")
async def compare_versions(
    strategy_id: str,
    a: int = Query(ge=1),
    b: int = Query(ge=1),
    container: Container = Depends(get_container),
) -> dict:
    with _translate():
        return await container.strategies.compare_versions(strategy_id, a, b)


@router.get("/{strategy_id}/audit")
async def get_audit(
    strategy_id: str, container: Container = Depends(get_container)
) -> list[dict]:
    with _translate():
        return await container.strategies.get_audit(strategy_id)
