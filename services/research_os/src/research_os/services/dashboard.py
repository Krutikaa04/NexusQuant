"""Dashboard read service (SPEC-007 §3 Research Dashboard).

Aggregates statistics and recent activity for the research workspace in one query pass.
Activity is derived from the append-only stores (status history + reviews), so the feed is
itself an audit-faithful view.
"""

from __future__ import annotations

from nexus_platform.db.session import Database
from research_os.domain.lifecycle import ProjectStatus
from research_os.repositories.projects import ProjectRepository
from research_os.repositories.reviews import ReviewRepository


class DashboardService:
    def __init__(self, database: Database) -> None:
        self._db = database

    async def snapshot(self) -> dict:
        async with self._db.session() as session:
            repo = ProjectRepository(session)
            projects = await repo.list_projects()
            history = await repo.recent_history(limit=25)
            reviews = await ReviewRepository(session).recent(limit=25)

            names = {p.id: p.name for p in projects}

            by_status: dict[str, int] = {s.value: 0 for s in ProjectStatus}
            hypothesis_count = 0
            experiment_count = 0
            running = 0
            completed = 0
            for p in projects:
                by_status[p.status] = by_status.get(p.status, 0) + 1
                hypothesis_count += sum(1 for h in p.hypotheses if not h.archived)
                experiment_count += len(p.experiments)
                running += sum(1 for e in p.experiments if e.status == "running")
                completed += sum(1 for e in p.experiments if e.status == "completed")

            activity = sorted(
                [
                    {
                        "kind": "transition",
                        "at": h.created_at.isoformat(),
                        "project_id": h.project_id,
                        "project": names.get(h.project_id, "—"),
                        "actor": h.actor,
                        "detail": (
                            f"{h.from_status} → {h.to_status}" if h.from_status else "created"
                        ),
                        "note": h.note,
                    }
                    for h in history
                ]
                + [
                    {
                        "kind": "review",
                        "at": r.created_at.isoformat(),
                        "project_id": r.project_id,
                        "project": names.get(r.project_id, "—"),
                        "actor": r.reviewer,
                        "detail": f"review: {r.decision} @ {r.stage}",
                        "note": r.comments[:140],
                    }
                    for r in reviews
                ],
                key=lambda a: a["at"],
                reverse=True,
            )[:25]

            return {
                "stats": {
                    "projects": len(projects),
                    "by_status": by_status,
                    "hypotheses": hypothesis_count,
                    "experiments": experiment_count,
                    "experiments_running": running,
                    "experiments_completed": completed,
                    "reviews": sum(len(p.reviews) for p in projects),
                },
                "activity": activity,
            }
