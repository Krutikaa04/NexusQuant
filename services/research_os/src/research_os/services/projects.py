"""Project service: CRUD, the lifecycle state machine, and promotion (SPEC-007 §4, §8).

Enforced business rules:
* project names are unique; owners are capped at ``MAX_PROJECTS_PER_USER`` live projects;
* Draft → Active requires at least one non-archived hypothesis;
* Production Candidate → Approved requires an approving review at that stage
  (when ``REVIEW_REQUIRED``);
* approved/retired projects are immutable (metadata edits rejected);
* every transition is recorded in the append-only status history;
* reaching Approved publishes ``StrategyPromoted`` (SPEC-007 §7).
"""

from __future__ import annotations

from nexus_shared.events.catalog import EventType
from nexus_shared.events.envelope import EventEnvelope
from nexus_shared.events.publisher import EventPublisher
from nexus_shared.primitives.time import utc_now
from nexus_platform.db.session import Database
from research_os.config import Settings
from research_os.db.models import ProjectRecord
from research_os.domain.errors import GovernanceError, ImmutableArtifactError, NotFoundError
from research_os.domain.lifecycle import (
    IMMUTABLE_STATUSES,
    ProjectStatus,
    validate_transition,
)
from research_os.repositories.projects import ProjectRepository
from research_os.repositories.reviews import ReviewRepository

PRODUCER = "research_os"


class ProjectService:
    def __init__(self, database: Database, publisher: EventPublisher, settings: Settings) -> None:
        self._db = database
        self._publisher = publisher
        self._settings = settings

    async def create(
        self,
        *,
        name: str,
        owner: str,
        description: str | None = None,
        tags: list[str] | None = None,
        metadata: dict | None = None,
    ) -> ProjectRecord:
        async with self._db.begin() as session:
            repo = ProjectRepository(session)
            if await repo.get_by_name(name) is not None:
                raise GovernanceError(f"a project named '{name}' already exists")
            if await repo.count_for_owner(owner) >= self._settings.max_projects_per_user:
                raise GovernanceError(
                    f"owner '{owner}' has reached the limit of "
                    f"{self._settings.max_projects_per_user} live projects"
                )
            project = await repo.create(
                name=name,
                owner=owner,
                description=description,
                tags=tags or [],
                metadata=metadata or {},
            )
            await repo.record_transition(
                project.id, from_status=None, to_status=ProjectStatus.DRAFT, actor=owner,
                note="project created",
            )
        await self._publisher.publish(
            EventEnvelope(
                event_type=EventType.RESEARCH_PROJECT_CREATED,
                producer=PRODUCER,
                aggregate_id=project.id,
                payload={
                    "project_id": project.id,
                    "name": project.name,
                    "owner": project.owner,
                    "tags": project.tags,
                },
            )
        )
        return project

    async def get(self, project_id: str) -> ProjectRecord:
        async with self._db.session() as session:
            project = await ProjectRepository(session).get_full(project_id)
        if project is None:
            raise NotFoundError(f"project '{project_id}' not found")
        return project

    async def list(
        self, *, status: ProjectStatus | None = None, owner: str | None = None
    ) -> list[ProjectRecord]:
        async with self._db.session() as session:
            return await ProjectRepository(session).list_projects(status=status, owner=owner)

    async def update(
        self,
        project_id: str,
        *,
        description: str | None = None,
        tags: list[str] | None = None,
        metadata: dict | None = None,
    ) -> ProjectRecord:
        async with self._db.begin() as session:
            repo = ProjectRepository(session)
            project = await repo.get_full(project_id)
            if project is None:
                raise NotFoundError(f"project '{project_id}' not found")
            self._assert_mutable(project)
            if description is not None:
                project.description = description
            if tags is not None:
                project.tags = tags
            if metadata is not None:
                project.extra = metadata
            project.updated_at = utc_now()
        return project

    async def transition(
        self, project_id: str, *, to_status: ProjectStatus, actor: str, note: str | None = None
    ) -> ProjectRecord:
        """Advance the lifecycle by one legal step, enforcing the stage guards."""
        async with self._db.begin() as session:
            repo = ProjectRepository(session)
            project = await repo.get_full(project_id)
            if project is None:
                raise NotFoundError(f"project '{project_id}' not found")
            current = ProjectStatus(project.status)

            validate_transition(current, to_status)  # raises IllegalTransitionError

            if current is ProjectStatus.DRAFT and to_status is ProjectStatus.ACTIVE:
                if await repo.active_hypothesis_count(project.id) == 0:
                    raise GovernanceError(
                        "a project requires at least one hypothesis before activation"
                    )

            if to_status is ProjectStatus.APPROVED and self._settings.review_required:
                approved = await ReviewRepository(session).has_approval_at_stage(
                    project.id, ProjectStatus.PRODUCTION_CANDIDATE
                )
                if not approved:
                    raise GovernanceError(
                        "promotion to approved requires an approving review at the "
                        "production_candidate stage"
                    )

            project.status = to_status.value
            project.updated_at = utc_now()
            await repo.record_transition(
                project.id, from_status=current, to_status=to_status, actor=actor, note=note
            )

        if to_status is ProjectStatus.APPROVED:
            await self._publisher.publish(
                EventEnvelope(
                    event_type=EventType.STRATEGY_PROMOTED,
                    producer=PRODUCER,
                    aggregate_id=project.id,
                    payload={
                        "project_id": project.id,
                        "name": project.name,
                        "from_status": current.value,
                        "to_status": to_status.value,
                        "actor": actor,
                    },
                )
            )
        return project

    async def history(self, project_id: str) -> list:
        async with self._db.session() as session:
            repo = ProjectRepository(session)
            if await repo.get(project_id) is None:
                raise NotFoundError(f"project '{project_id}' not found")
            return await repo.history_for(project_id)

    @staticmethod
    def _assert_mutable(project: ProjectRecord) -> None:
        if ProjectStatus(project.status) in IMMUTABLE_STATUSES:
            raise ImmutableArtifactError(
                f"project '{project.name}' is {project.status}; research artifacts are immutable"
            )
