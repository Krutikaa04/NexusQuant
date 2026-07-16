"""Hypothesis service (SPEC-007 §2): create, edit, archive; frozen after project approval."""

from __future__ import annotations

from nexus_shared.events.catalog import EventType
from nexus_shared.events.envelope import EventEnvelope
from nexus_shared.events.publisher import EventPublisher
from nexus_shared.primitives.time import utc_now
from nexus_platform.db.session import Database
from research_os.db.models import HypothesisRecord
from research_os.domain.errors import ImmutableArtifactError, NotFoundError
from research_os.domain.lifecycle import IMMUTABLE_STATUSES, ProjectStatus
from research_os.repositories.projects import ProjectRepository
from research_os.services.projects import PRODUCER


class HypothesisService:
    def __init__(self, database: Database, publisher: EventPublisher) -> None:
        self._db = database
        self._publisher = publisher

    async def create(
        self,
        *,
        project_id: str,
        statement: str,
        success_criteria: str,
        notes: str | None = None,
    ) -> HypothesisRecord:
        async with self._db.begin() as session:
            repo = ProjectRepository(session)
            project = await repo.get(project_id)
            if project is None:
                raise NotFoundError(f"project '{project_id}' not found")
            self._assert_project_mutable(project)
            hypothesis = await repo.add_hypothesis(
                project, statement=statement, success_criteria=success_criteria, notes=notes
            )
        await self._publisher.publish(
            EventEnvelope(
                event_type=EventType.HYPOTHESIS_CREATED,
                producer=PRODUCER,
                aggregate_id=project_id,
                payload={
                    "hypothesis_id": hypothesis.id,
                    "project_id": project_id,
                    "statement": statement,
                    "success_criteria": success_criteria,
                },
            )
        )
        return hypothesis

    async def update(
        self,
        hypothesis_id: str,
        *,
        statement: str | None = None,
        success_criteria: str | None = None,
        notes: str | None = None,
        archived: bool | None = None,
    ) -> HypothesisRecord:
        async with self._db.begin() as session:
            repo = ProjectRepository(session)
            hypothesis = await repo.get_hypothesis(hypothesis_id)
            if hypothesis is None:
                raise NotFoundError(f"hypothesis '{hypothesis_id}' not found")
            project = await repo.get(hypothesis.project_id)
            self._assert_project_mutable(project)
            if statement is not None:
                hypothesis.statement = statement
            if success_criteria is not None:
                hypothesis.success_criteria = success_criteria
            if notes is not None:
                hypothesis.notes = notes
            if archived is not None:
                hypothesis.archived = archived
            hypothesis.updated_at = utc_now()
            project.updated_at = utc_now()
        return hypothesis

    @staticmethod
    def _assert_project_mutable(project) -> None:
        if ProjectStatus(project.status) in IMMUTABLE_STATUSES:
            raise ImmutableArtifactError(
                f"project '{project.name}' is {project.status}; hypotheses are immutable"
            )
