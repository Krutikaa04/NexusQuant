"""Repository over immutable research reviews (SPEC-007 §5).

Reviews are append-only: there is deliberately no update or delete method on this
repository — immutability is enforced at the boundary, not by convention.
"""

from __future__ import annotations

from uuid import uuid4

from sqlalchemy import select

from nexus_platform.db.repository import BaseRepository
from nexus_shared.primitives.time import utc_now
from research_os.db.models import ProjectRecord, ReviewRecord
from research_os.domain.lifecycle import ProjectStatus
from research_os.domain.vocabulary import ReviewDecision


class ReviewRepository(BaseRepository[ReviewRecord]):
    model = ReviewRecord

    async def add_review(
        self,
        project: ProjectRecord,
        *,
        reviewer: str,
        decision: ReviewDecision,
        comments: str,
    ) -> ReviewRecord:
        record = ReviewRecord(
            id=str(uuid4()),
            project_id=project.id,
            reviewer=reviewer,
            decision=decision.value,
            comments=comments,
            stage=project.status,
            created_at=utc_now(),
        )
        self.session.add(record)
        project.updated_at = utc_now()
        await self.session.flush()
        return record

    async def reviews_for(self, project_id: str) -> list[ReviewRecord]:
        stmt = (
            select(ReviewRecord)
            .where(ReviewRecord.project_id == project_id)
            .order_by(ReviewRecord.created_at.desc())
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def has_approval_at_stage(self, project_id: str, stage: ProjectStatus) -> bool:
        """True when the project has an approving review recorded at the given stage."""
        stmt = select(ReviewRecord).where(
            ReviewRecord.project_id == project_id,
            ReviewRecord.stage == stage.value,
            ReviewRecord.decision == ReviewDecision.APPROVE.value,
        )
        return (await self.session.execute(stmt)).scalars().first() is not None

    async def recent(self, limit: int = 20) -> list[ReviewRecord]:
        stmt = select(ReviewRecord).order_by(ReviewRecord.created_at.desc()).limit(limit)
        return list((await self.session.execute(stmt)).scalars().all())
