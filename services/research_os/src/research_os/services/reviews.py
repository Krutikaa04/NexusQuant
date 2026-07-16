"""Review service (SPEC-007 §2, §5): the immutable governance record.

A review is written once and never modified — there is no update path anywhere in this
context. Each review captures the project's lifecycle stage at the time, which is what the
promotion guard checks (an approval at ``production_candidate`` unlocks Approved).
"""

from __future__ import annotations

from nexus_shared.events.catalog import EventType
from nexus_shared.events.envelope import EventEnvelope
from nexus_shared.events.publisher import EventPublisher
from nexus_platform.db.session import Database
from research_os.db.models import ReviewRecord
from research_os.domain.errors import GovernanceError, NotFoundError
from research_os.domain.lifecycle import ProjectStatus
from research_os.domain.vocabulary import ReviewDecision
from research_os.repositories.projects import ProjectRepository
from research_os.repositories.reviews import ReviewRepository
from research_os.services.projects import PRODUCER


class ReviewService:
    def __init__(self, database: Database, publisher: EventPublisher) -> None:
        self._db = database
        self._publisher = publisher

    async def create(
        self,
        *,
        project_id: str,
        reviewer: str,
        decision: ReviewDecision,
        comments: str,
    ) -> ReviewRecord:
        if not comments.strip():
            raise GovernanceError("a review requires comments explaining the decision")
        async with self._db.begin() as session:
            project = await ProjectRepository(session).get(project_id)
            if project is None:
                raise NotFoundError(f"project '{project_id}' not found")
            if ProjectStatus(project.status) is ProjectStatus.RETIRED:
                raise GovernanceError("retired projects cannot be reviewed")
            review = await ReviewRepository(session).add_review(
                project, reviewer=reviewer, decision=decision, comments=comments
            )
        await self._publisher.publish(
            EventEnvelope(
                event_type=EventType.RESEARCH_REVIEWED,
                producer=PRODUCER,
                aggregate_id=project_id,
                payload={
                    "review_id": review.id,
                    "project_id": project_id,
                    "reviewer": reviewer,
                    "decision": decision.value,
                    "stage": review.stage,
                },
            )
        )
        return review

    async def list_for(self, project_id: str) -> list[ReviewRecord]:
        async with self._db.session() as session:
            if await ProjectRepository(session).get(project_id) is None:
                raise NotFoundError(f"project '{project_id}' not found")
            return await ReviewRepository(session).reviews_for(project_id)
