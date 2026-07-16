"""Repository over projects, hypotheses, experiments, and status history (SPEC-007 §5)."""

from __future__ import annotations

from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from nexus_platform.db.repository import BaseRepository
from nexus_shared.primitives.time import utc_now
from research_os.db.models import (
    ExperimentRecord,
    HypothesisRecord,
    ProjectRecord,
    StatusHistoryRecord,
)
from research_os.domain.lifecycle import ProjectStatus


class ProjectRepository(BaseRepository[ProjectRecord]):
    model = ProjectRecord

    async def get_full(self, project_id: str) -> ProjectRecord | None:
        stmt = (
            select(ProjectRecord)
            .where(ProjectRecord.id == project_id)
            .options(
                selectinload(ProjectRecord.hypotheses),
                selectinload(ProjectRecord.experiments),
                selectinload(ProjectRecord.reviews),
            )
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_by_name(self, name: str) -> ProjectRecord | None:
        stmt = select(ProjectRecord).where(ProjectRecord.name == name)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def list_projects(
        self,
        *,
        status: ProjectStatus | None = None,
        owner: str | None = None,
    ) -> list[ProjectRecord]:
        stmt = select(ProjectRecord).options(
            selectinload(ProjectRecord.hypotheses),
            selectinload(ProjectRecord.experiments),
            selectinload(ProjectRecord.reviews),
        )
        if status is not None:
            stmt = stmt.where(ProjectRecord.status == status.value)
        if owner is not None:
            stmt = stmt.where(ProjectRecord.owner == owner)
        stmt = stmt.order_by(ProjectRecord.updated_at.desc())
        return list((await self.session.execute(stmt)).scalars().all())

    async def count_for_owner(self, owner: str) -> int:
        stmt = (
            select(func.count())
            .select_from(ProjectRecord)
            .where(ProjectRecord.owner == owner, ProjectRecord.status != "retired")
        )
        return int((await self.session.execute(stmt)).scalar_one())

    async def create(
        self,
        *,
        name: str,
        owner: str,
        description: str | None,
        tags: list[str],
        metadata: dict,
    ) -> ProjectRecord:
        now = utc_now()
        record = ProjectRecord(
            id=str(uuid4()),
            name=name,
            owner=owner,
            description=description,
            status=ProjectStatus.DRAFT.value,
            tags=tags,
            extra=metadata,
            created_at=now,
            updated_at=now,
        )
        return await self.add(record)

    # --- hypotheses ---

    async def add_hypothesis(
        self,
        project: ProjectRecord,
        *,
        statement: str,
        success_criteria: str,
        notes: str | None,
    ) -> HypothesisRecord:
        now = utc_now()
        record = HypothesisRecord(
            id=str(uuid4()),
            project_id=project.id,
            statement=statement,
            success_criteria=success_criteria,
            notes=notes,
            archived=False,
            created_at=now,
            updated_at=now,
        )
        self.session.add(record)
        project.updated_at = now
        await self.session.flush()
        return record

    async def get_hypothesis(self, hypothesis_id: str) -> HypothesisRecord | None:
        return await self.session.get(HypothesisRecord, hypothesis_id)

    async def active_hypothesis_count(self, project_id: str) -> int:
        stmt = (
            select(func.count())
            .select_from(HypothesisRecord)
            .where(
                HypothesisRecord.project_id == project_id,
                HypothesisRecord.archived.is_(False),
            )
        )
        return int((await self.session.execute(stmt)).scalar_one())

    # --- experiments ---

    async def add_experiment(
        self,
        project: ProjectRecord,
        *,
        name: str,
        dataset_version: str,
        feature_version: str,
        hypothesis_id: str | None,
        notes: str | None,
    ) -> ExperimentRecord:
        now = utc_now()
        record = ExperimentRecord(
            id=str(uuid4()),
            project_id=project.id,
            hypothesis_id=hypothesis_id,
            name=name,
            dataset_version=dataset_version,
            feature_version=feature_version,
            status="pending",
            metrics={},
            notes=notes,
            created_at=now,
        )
        self.session.add(record)
        project.updated_at = now
        await self.session.flush()
        return record

    async def get_experiment(self, experiment_id: str) -> ExperimentRecord | None:
        return await self.session.get(ExperimentRecord, experiment_id)

    # --- status history ---

    async def record_transition(
        self,
        project_id: str,
        *,
        from_status: ProjectStatus | None,
        to_status: ProjectStatus,
        actor: str,
        note: str | None = None,
    ) -> StatusHistoryRecord:
        record = StatusHistoryRecord(
            id=str(uuid4()),
            project_id=project_id,
            from_status=from_status.value if from_status else None,
            to_status=to_status.value,
            actor=actor,
            note=note,
            created_at=utc_now(),
        )
        self.session.add(record)
        await self.session.flush()
        return record

    async def history_for(self, project_id: str) -> list[StatusHistoryRecord]:
        stmt = (
            select(StatusHistoryRecord)
            .where(StatusHistoryRecord.project_id == project_id)
            .order_by(StatusHistoryRecord.created_at.asc())
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def recent_history(self, limit: int = 30) -> list[StatusHistoryRecord]:
        stmt = (
            select(StatusHistoryRecord)
            .order_by(StatusHistoryRecord.created_at.desc())
            .limit(limit)
        )
        return list((await self.session.execute(stmt)).scalars().all())
