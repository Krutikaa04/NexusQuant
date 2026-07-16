"""REST routes for the Research OS (SPEC-007 §6). Controllers are thin: translate HTTP,
delegate to services, map domain errors to status codes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from starlette import status

from research_os.api.dto import (
    ExperimentComplete,
    ExperimentCreate,
    ExperimentUpdate,
    ExperimentView,
    HealthResponse,
    HypothesisCreate,
    HypothesisUpdate,
    HypothesisView,
    ProjectCreate,
    ProjectDetail,
    ProjectSummary,
    ProjectUpdate,
    ReviewCreate,
    ReviewView,
    TransitionRequest,
    TransitionView,
)
from research_os.container import Container
from research_os.domain.errors import GovernanceError, NotFoundError
from research_os.domain.lifecycle import IllegalTransitionError, ProjectStatus
from research_os.security import Principal, require_principal

router = APIRouter(prefix="/research", tags=["research-os"])


def get_container(request: Request) -> Container:
    return request.app.state.research_container


def _map_errors(exc: Exception) -> HTTPException:
    if isinstance(exc, NotFoundError):
        return HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, IllegalTransitionError):
        return HTTPException(status.HTTP_409_CONFLICT, detail=str(exc))
    if isinstance(exc, GovernanceError):
        return HTTPException(status.HTTP_409_CONFLICT, detail=str(exc))
    raise exc


@router.get("/health", response_model=HealthResponse)
async def health(container: Container = Depends(get_container)) -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=container.settings.service_name,
        environment=container.settings.environment,
        migrations_applied=container.applied_migrations,
    )


# --- projects (SPEC-007 §6) ---


@router.post("/projects", response_model=ProjectSummary, status_code=status.HTTP_201_CREATED)
async def create_project(
    body: ProjectCreate,
    container: Container = Depends(get_container),
    principal: Principal = Depends(require_principal),
) -> ProjectSummary:
    try:
        project = await container.projects.create(
            name=body.name, owner=body.owner, description=body.description,
            tags=body.tags, metadata=body.metadata,
        )
        full = await container.projects.get(project.id)
    except Exception as exc:  # noqa: BLE001 - mapped below
        raise _map_errors(exc)
    return ProjectSummary.of(full)


@router.get("/projects", response_model=list[ProjectSummary])
async def list_projects(
    status_filter: ProjectStatus | None = None,
    owner: str | None = None,
    container: Container = Depends(get_container),
) -> list[ProjectSummary]:
    projects = await container.projects.list(status=status_filter, owner=owner)
    return [ProjectSummary.of(p) for p in projects]


@router.get("/projects/{project_id}", response_model=ProjectDetail)
async def get_project(
    project_id: str, container: Container = Depends(get_container)
) -> ProjectDetail:
    try:
        project = await container.projects.get(project_id)
    except Exception as exc:  # noqa: BLE001
        raise _map_errors(exc)
    return ProjectDetail.of_full(project)


@router.patch("/projects/{project_id}", response_model=ProjectSummary)
async def update_project(
    project_id: str,
    body: ProjectUpdate,
    container: Container = Depends(get_container),
    principal: Principal = Depends(require_principal),
) -> ProjectSummary:
    try:
        await container.projects.update(
            project_id, description=body.description, tags=body.tags, metadata=body.metadata
        )
        project = await container.projects.get(project_id)
    except Exception as exc:  # noqa: BLE001
        raise _map_errors(exc)
    return ProjectSummary.of(project)


@router.post("/projects/{project_id}/transition", response_model=ProjectSummary)
async def transition_project(
    project_id: str,
    body: TransitionRequest,
    container: Container = Depends(get_container),
    principal: Principal = Depends(require_principal),
) -> ProjectSummary:
    try:
        await container.projects.transition(
            project_id, to_status=body.to_status, actor=body.actor, note=body.note
        )
        project = await container.projects.get(project_id)
    except Exception as exc:  # noqa: BLE001
        raise _map_errors(exc)
    return ProjectSummary.of(project)


@router.get("/projects/{project_id}/history", response_model=list[TransitionView])
async def project_history(
    project_id: str, container: Container = Depends(get_container)
) -> list[TransitionView]:
    try:
        history = await container.projects.history(project_id)
    except Exception as exc:  # noqa: BLE001
        raise _map_errors(exc)
    return [TransitionView.of(t) for t in history]


# --- hypotheses ---


@router.post("/hypotheses", response_model=HypothesisView, status_code=status.HTTP_201_CREATED)
async def create_hypothesis(
    body: HypothesisCreate,
    container: Container = Depends(get_container),
    principal: Principal = Depends(require_principal),
) -> HypothesisView:
    try:
        hypothesis = await container.hypotheses.create(
            project_id=body.project_id, statement=body.statement,
            success_criteria=body.success_criteria, notes=body.notes,
        )
    except Exception as exc:  # noqa: BLE001
        raise _map_errors(exc)
    return HypothesisView.of(hypothesis)


@router.patch("/hypotheses/{hypothesis_id}", response_model=HypothesisView)
async def update_hypothesis(
    hypothesis_id: str,
    body: HypothesisUpdate,
    container: Container = Depends(get_container),
    principal: Principal = Depends(require_principal),
) -> HypothesisView:
    try:
        hypothesis = await container.hypotheses.update(
            hypothesis_id, statement=body.statement,
            success_criteria=body.success_criteria, notes=body.notes, archived=body.archived,
        )
    except Exception as exc:  # noqa: BLE001
        raise _map_errors(exc)
    return HypothesisView.of(hypothesis)


# --- experiments ---


@router.post("/experiments", response_model=ExperimentView, status_code=status.HTTP_201_CREATED)
async def create_experiment(
    body: ExperimentCreate,
    container: Container = Depends(get_container),
    principal: Principal = Depends(require_principal),
) -> ExperimentView:
    try:
        experiment = await container.experiments.create(
            project_id=body.project_id, name=body.name,
            dataset_version=body.dataset_version, feature_version=body.feature_version,
            hypothesis_id=body.hypothesis_id, notes=body.notes,
        )
    except Exception as exc:  # noqa: BLE001
        raise _map_errors(exc)
    return ExperimentView.of(experiment)


@router.patch("/experiments/{experiment_id}", response_model=ExperimentView)
async def update_experiment(
    experiment_id: str,
    body: ExperimentUpdate,
    container: Container = Depends(get_container),
    principal: Principal = Depends(require_principal),
) -> ExperimentView:
    try:
        experiment = await container.experiments.update(
            experiment_id, name=body.name, notes=body.notes
        )
    except Exception as exc:  # noqa: BLE001
        raise _map_errors(exc)
    return ExperimentView.of(experiment)


@router.post("/experiments/{experiment_id}/start", response_model=ExperimentView)
async def start_experiment(
    experiment_id: str,
    container: Container = Depends(get_container),
    principal: Principal = Depends(require_principal),
) -> ExperimentView:
    try:
        experiment = await container.experiments.start(experiment_id)
    except Exception as exc:  # noqa: BLE001
        raise _map_errors(exc)
    return ExperimentView.of(experiment)


@router.post("/experiments/{experiment_id}/complete", response_model=ExperimentView)
async def complete_experiment(
    experiment_id: str,
    body: ExperimentComplete,
    container: Container = Depends(get_container),
    principal: Principal = Depends(require_principal),
) -> ExperimentView:
    try:
        experiment = await container.experiments.complete(
            experiment_id, status=body.status, metrics=body.metrics, notes=body.notes
        )
    except Exception as exc:  # noqa: BLE001
        raise _map_errors(exc)
    return ExperimentView.of(experiment)


# --- reviews ---


@router.post("/reviews", response_model=ReviewView, status_code=status.HTTP_201_CREATED)
async def create_review(
    body: ReviewCreate,
    container: Container = Depends(get_container),
    principal: Principal = Depends(require_principal),
) -> ReviewView:
    try:
        review = await container.reviews.create(
            project_id=body.project_id, reviewer=body.reviewer,
            decision=body.decision, comments=body.comments,
        )
    except Exception as exc:  # noqa: BLE001
        raise _map_errors(exc)
    return ReviewView.of(review)


@router.get("/projects/{project_id}/reviews", response_model=list[ReviewView])
async def project_reviews(
    project_id: str, container: Container = Depends(get_container)
) -> list[ReviewView]:
    try:
        reviews = await container.reviews.list_for(project_id)
    except Exception as exc:  # noqa: BLE001
        raise _map_errors(exc)
    return [ReviewView.of(r) for r in reviews]


# --- dashboard (SPEC-007 §3) ---


@router.get("/dashboard")
async def dashboard(container: Container = Depends(get_container)) -> dict:
    return await container.dashboard.snapshot()
