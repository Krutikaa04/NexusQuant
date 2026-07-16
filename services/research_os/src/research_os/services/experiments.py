"""Experiment service (SPEC-007 §2, §8): metadata and lifecycle only — the actual
validation engine is the Validation Platform's concern (out of scope here).

Rules enforced:
* every experiment belongs to one project, created only while the project is in an
  experimentation-capable status (active / experimenting);
* dataset and feature versions are explicit and required (SPEC-007 §8);
* run status moves pending → running → completed|failed|cancelled; terminal is final;
* ``ExperimentStarted`` / ``ExperimentCompleted`` are published on those edges (§7).
"""

from __future__ import annotations

from nexus_shared.events.catalog import EventType
from nexus_shared.events.envelope import EventEnvelope
from nexus_shared.events.publisher import EventPublisher
from nexus_shared.primitives.time import utc_now
from nexus_platform.db.session import Database
from research_os.db.models import ExperimentRecord
from research_os.domain.errors import GovernanceError, ImmutableArtifactError, NotFoundError
from research_os.domain.lifecycle import (
    EXPERIMENTATION_STATUSES,
    IMMUTABLE_STATUSES,
    ProjectStatus,
)
from research_os.domain.vocabulary import (
    TERMINAL_EXPERIMENT_STATUSES,
    ExperimentStatus,
)
from research_os.repositories.projects import ProjectRepository
from research_os.services.projects import PRODUCER


class ExperimentService:
    def __init__(self, database: Database, publisher: EventPublisher) -> None:
        self._db = database
        self._publisher = publisher

    async def create(
        self,
        *,
        project_id: str,
        name: str,
        dataset_version: str,
        feature_version: str,
        hypothesis_id: str | None = None,
        notes: str | None = None,
    ) -> ExperimentRecord:
        if not dataset_version.strip() or not feature_version.strip():
            raise GovernanceError(
                "experiments must reference explicit dataset and feature versions"
            )
        async with self._db.begin() as session:
            repo = ProjectRepository(session)
            project = await repo.get(project_id)
            if project is None:
                raise NotFoundError(f"project '{project_id}' not found")
            status = ProjectStatus(project.status)
            if status in IMMUTABLE_STATUSES:
                raise ImmutableArtifactError(
                    f"project '{project.name}' is {project.status}; experiments are immutable"
                )
            if status not in EXPERIMENTATION_STATUSES:
                raise GovernanceError(
                    f"experiments can only be created while a project is active or "
                    f"experimenting (current: {project.status})"
                )
            if hypothesis_id is not None:
                hypothesis = await repo.get_hypothesis(hypothesis_id)
                if hypothesis is None or hypothesis.project_id != project_id:
                    raise NotFoundError(
                        f"hypothesis '{hypothesis_id}' not found in project '{project_id}'"
                    )
            experiment = await repo.add_experiment(
                project,
                name=name,
                dataset_version=dataset_version,
                feature_version=feature_version,
                hypothesis_id=hypothesis_id,
                notes=notes,
            )
        return experiment

    async def start(self, experiment_id: str) -> ExperimentRecord:
        async with self._db.begin() as session:
            repo = ProjectRepository(session)
            experiment = await self._get(repo, experiment_id)
            if ExperimentStatus(experiment.status) is not ExperimentStatus.PENDING:
                raise GovernanceError(
                    f"experiment is {experiment.status}; only pending experiments can start"
                )
            experiment.status = ExperimentStatus.RUNNING.value
            experiment.started_at = utc_now()
        await self._publisher.publish(
            EventEnvelope(
                event_type=EventType.EXPERIMENT_STARTED,
                producer=PRODUCER,
                aggregate_id=experiment.project_id,
                payload={
                    "experiment_id": experiment.id,
                    "project_id": experiment.project_id,
                    "name": experiment.name,
                    "dataset_version": experiment.dataset_version,
                    "feature_version": experiment.feature_version,
                },
            )
        )
        return experiment

    async def complete(
        self,
        experiment_id: str,
        *,
        status: ExperimentStatus,
        metrics: dict | None = None,
        notes: str | None = None,
    ) -> ExperimentRecord:
        if status not in TERMINAL_EXPERIMENT_STATUSES:
            raise GovernanceError(
                f"'{status.value}' is not a terminal status; use completed/failed/cancelled"
            )
        async with self._db.begin() as session:
            repo = ProjectRepository(session)
            experiment = await self._get(repo, experiment_id)
            current = ExperimentStatus(experiment.status)
            if current in TERMINAL_EXPERIMENT_STATUSES:
                raise GovernanceError(f"experiment already finished ({current.value})")
            if current is not ExperimentStatus.RUNNING:
                raise GovernanceError("only a running experiment can be completed")
            experiment.status = status.value
            experiment.metrics = metrics or {}
            if notes is not None:
                experiment.notes = notes
            experiment.completed_at = utc_now()
        await self._publisher.publish(
            EventEnvelope(
                event_type=EventType.EXPERIMENT_COMPLETED,
                producer=PRODUCER,
                aggregate_id=experiment.project_id,
                payload={
                    "experiment_id": experiment.id,
                    "project_id": experiment.project_id,
                    "status": experiment.status,
                    "metrics": experiment.metrics,
                },
            )
        )
        return experiment

    async def update(
        self, experiment_id: str, *, name: str | None = None, notes: str | None = None
    ) -> ExperimentRecord:
        """Edit descriptive metadata; version references and results are immutable."""
        async with self._db.begin() as session:
            repo = ProjectRepository(session)
            experiment = await self._get(repo, experiment_id)
            project = await repo.get(experiment.project_id)
            if ProjectStatus(project.status) in IMMUTABLE_STATUSES:
                raise ImmutableArtifactError(
                    f"project '{project.name}' is {project.status}; experiments are immutable"
                )
            if name is not None:
                experiment.name = name
            if notes is not None:
                experiment.notes = notes
        return experiment

    @staticmethod
    async def _get(repo: ProjectRepository, experiment_id: str) -> ExperimentRecord:
        experiment = await repo.get_experiment(experiment_id)
        if experiment is None:
            raise NotFoundError(f"experiment '{experiment_id}' not found")
        return experiment
