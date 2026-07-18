"""Strategy application service — all strategy business logic lives here.

Controllers are thin and delegate to this service. Writes run inside a single transaction
(``database.begin``) so a strategy, its version, its health row, and the audit record commit
atomically. Every structural change and lifecycle transition is recorded in the audit trail.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from nexus_platform.db.session import Database
from strategy_core.config import Settings
from strategy_core.db.models import (
    StrategyAuditRecord,
    StrategyHealthRecord,
    StrategyRecord,
    StrategyVersionRecord,
)
from strategy_core.domain.errors import (
    IllegalTransition,
    ImmutableStrategy,
    StrategyNotFound,
    ValidationError,
)
from strategy_core.domain.lifecycle import (
    StrategyStatus,
    allowed_transitions,
    can_transition,
    is_editable,
    is_terminal,
)
from strategy_core.domain.models import StrategyConfig
from strategy_core.repositories.audit import StrategyAuditRepository
from strategy_core.repositories.strategies import (
    StrategyHealthRepository,
    StrategyRepository,
    StrategyVersionRepository,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> str:
    return str(uuid.uuid4())


def _iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt is not None else None


class StrategyService:
    def __init__(self, database: Database, settings: Settings) -> None:
        self._db = database
        self._settings = settings

    # ---- commands -------------------------------------------------------

    async def create_strategy(
        self,
        *,
        name: str,
        description: str = "",
        category: str | None = None,
        owner: str = "unknown",
        tags: list[str] | None = None,
        config: StrategyConfig | None = None,
        actor: str = "unknown",
    ) -> dict:
        name = (name or "").strip()
        if not name:
            raise ValidationError("name is required")
        category = (category or self._settings.default_category).strip() or "uncategorized"
        cfg = (config or StrategyConfig()).normalized()
        tags = _clean_tags(tags)
        sid = _uuid()
        now = _now()

        async with self._db.begin() as session:
            strategies = StrategyRepository(session)
            if await strategies.count() >= self._settings.max_strategies:
                raise ValidationError("maximum number of strategies reached")
            versions = StrategyVersionRepository(session)
            health = StrategyHealthRepository(session)
            audit = StrategyAuditRepository(session)

            await strategies.add(
                StrategyRecord(
                    id=sid, name=name, description=description or "", category=category,
                    owner=owner or "unknown", status=StrategyStatus.DRAFT.value, tags=tags,
                    current_version=1, created_at=now, updated_at=now, deleted_at=None,
                )
            )
            await versions.add(
                _new_version_record(
                    sid, 1, name, description or "", category, tags, cfg,
                    "Initial version", actor, now,
                )
            )
            await health.add(
                StrategyHealthRecord(
                    strategy_id=sid, health_score=None, last_evaluation=None,
                    last_execution=None, consecutive_failures=0, consecutive_successes=0,
                    enabled=True, trading_allowed=False, updated_at=now,
                )
            )
            await _record_audit(
                audit, sid, action="created", to_status=StrategyStatus.DRAFT.value,
                version=1, actor=actor, detail="Strategy created", at=now,
            )
        return await self.get_detail(sid)

    async def update_strategy(
        self,
        strategy_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        category: str | None = None,
        tags: list[str] | None = None,
        config: StrategyConfig | None = None,
        change_summary: str = "",
        actor: str = "unknown",
    ) -> dict:
        now = _now()
        async with self._db.begin() as session:
            strategies = StrategyRepository(session)
            versions = StrategyVersionRepository(session)
            audit = StrategyAuditRepository(session)
            record = await strategies.get_active(strategy_id)
            if record is None:
                raise StrategyNotFound(strategy_id)
            if not is_editable(StrategyStatus(record.status)):
                raise ImmutableStrategy(
                    f"strategy is {record.status} and cannot be modified"
                )
            current = await versions.get_version(strategy_id, record.current_version)
            base_config = StrategyConfig(**(current.config if current else {}))

            new_name = (name if name is not None else record.name).strip() or record.name
            new_desc = description if description is not None else record.description
            new_cat = (category if category is not None else record.category).strip() or record.category
            new_tags = _clean_tags(tags) if tags is not None else list(record.tags or [])
            new_cfg = (config if config is not None else base_config).normalized()
            new_version = record.current_version + 1

            await versions.add(
                _new_version_record(
                    strategy_id, new_version, new_name, new_desc, new_cat, new_tags,
                    new_cfg, change_summary or "Configuration updated", actor, now,
                )
            )
            record.name = new_name
            record.description = new_desc
            record.category = new_cat
            record.tags = new_tags
            record.current_version = new_version
            record.updated_at = now
            await _record_audit(
                audit, strategy_id, action="updated", from_status=record.status,
                to_status=record.status, version=new_version, actor=actor,
                detail=change_summary or "Configuration updated", at=now,
            )
        return await self.get_detail(strategy_id)

    async def transition(
        self, strategy_id: str, *, to_status: str, reason: str = "", actor: str = "unknown"
    ) -> dict:
        try:
            target = StrategyStatus(to_status)
        except ValueError as exc:
            raise ValidationError(f"unknown status '{to_status}'") from exc
        now = _now()
        async with self._db.begin() as session:
            strategies = StrategyRepository(session)
            audit = StrategyAuditRepository(session)
            record = await strategies.get_active(strategy_id)
            if record is None:
                raise StrategyNotFound(strategy_id)
            current = StrategyStatus(record.status)
            if not can_transition(current, target):
                raise IllegalTransition(
                    f"cannot move from {current.value} to {target.value}"
                )
            record.status = target.value
            record.updated_at = now
            await _record_audit(
                audit, strategy_id, action="transition", from_status=current.value,
                to_status=target.value, version=record.current_version, actor=actor,
                detail=reason or f"Transitioned to {target.value}", at=now,
            )
        return await self.get_detail(strategy_id)

    async def rollback(
        self, strategy_id: str, *, to_version: int, actor: str = "unknown"
    ) -> dict:
        now = _now()
        async with self._db.begin() as session:
            strategies = StrategyRepository(session)
            versions = StrategyVersionRepository(session)
            audit = StrategyAuditRepository(session)
            record = await strategies.get_active(strategy_id)
            if record is None:
                raise StrategyNotFound(strategy_id)
            if not is_editable(StrategyStatus(record.status)):
                raise ImmutableStrategy(
                    f"strategy is {record.status} and cannot be modified"
                )
            source = await versions.get_version(strategy_id, to_version)
            if source is None:
                raise StrategyNotFound(f"{strategy_id} v{to_version}")
            new_version = record.current_version + 1
            await versions.add(
                _new_version_record(
                    strategy_id, new_version, source.name, source.description,
                    source.category, list(source.tags or []),
                    StrategyConfig(**source.config), f"Rollback to v{to_version}", actor, now,
                )
            )
            record.name = source.name
            record.description = source.description
            record.category = source.category
            record.tags = list(source.tags or [])
            record.current_version = new_version
            record.updated_at = now
            await _record_audit(
                audit, strategy_id, action="rollback", from_status=record.status,
                to_status=record.status, version=new_version, actor=actor,
                detail=f"Rolled back to v{to_version}", at=now,
            )
        return await self.get_detail(strategy_id)

    async def clone_strategy(
        self, strategy_id: str, *, new_name: str, actor: str = "unknown"
    ) -> dict:
        new_name = (new_name or "").strip()
        if not new_name:
            raise ValidationError("new_name is required")
        now = _now()
        new_id = _uuid()
        async with self._db.begin() as session:
            strategies = StrategyRepository(session)
            versions = StrategyVersionRepository(session)
            health = StrategyHealthRepository(session)
            audit = StrategyAuditRepository(session)
            source = await strategies.get_active(strategy_id)
            if source is None:
                raise StrategyNotFound(strategy_id)
            source_version = await versions.get_version(strategy_id, source.current_version)
            cfg = StrategyConfig(**(source_version.config if source_version else {}))
            await strategies.add(
                StrategyRecord(
                    id=new_id, name=new_name, description=source.description,
                    category=source.category, owner=source.owner,
                    status=StrategyStatus.DRAFT.value, tags=list(source.tags or []),
                    current_version=1, created_at=now, updated_at=now, deleted_at=None,
                )
            )
            await versions.add(
                _new_version_record(
                    new_id, 1, new_name, source.description, source.category,
                    list(source.tags or []), cfg, f"Cloned from {strategy_id}", actor, now,
                )
            )
            await health.add(
                StrategyHealthRecord(
                    strategy_id=new_id, health_score=None, last_evaluation=None,
                    last_execution=None, consecutive_failures=0, consecutive_successes=0,
                    enabled=True, trading_allowed=False, updated_at=now,
                )
            )
            await _record_audit(
                audit, new_id, action="cloned", to_status=StrategyStatus.DRAFT.value,
                version=1, actor=actor, detail=f"Cloned from {strategy_id}", at=now,
            )
        return await self.get_detail(new_id)

    async def soft_delete(self, strategy_id: str, *, actor: str = "unknown") -> None:
        now = _now()
        async with self._db.begin() as session:
            strategies = StrategyRepository(session)
            audit = StrategyAuditRepository(session)
            record = await strategies.get_active(strategy_id)
            if record is None:
                raise StrategyNotFound(strategy_id)
            record.deleted_at = now
            record.updated_at = now
            await _record_audit(
                audit, strategy_id, action="deleted", from_status=record.status,
                to_status=record.status, version=record.current_version, actor=actor,
                detail="Strategy soft-deleted", at=now,
            )

    # ---- queries --------------------------------------------------------

    async def list_strategies(
        self,
        *,
        status: str | None = None,
        category: str | None = None,
        owner: str | None = None,
        tag: str | None = None,
    ) -> list[dict]:
        async with self._db.session() as session:
            strategies = StrategyRepository(session)
            health = StrategyHealthRepository(session)
            rows = await strategies.list_filtered(
                status=status, category=category, owner=owner, tag=tag
            )
            out = []
            for r in rows:
                h = await health.get_for(r.id)
                out.append(_summary_dict(r, h))
            return out

    async def get_detail(self, strategy_id: str) -> dict:
        async with self._db.session() as session:
            strategies = StrategyRepository(session)
            versions = StrategyVersionRepository(session)
            health = StrategyHealthRepository(session)
            record = await strategies.get_active(strategy_id)
            if record is None:
                raise StrategyNotFound(strategy_id)
            current = await versions.get_version(strategy_id, record.current_version)
            version_rows = await versions.list_for(strategy_id)
            h = await health.get_for(strategy_id)
            cfg = current.config if current else {}
            summary = _summary_dict(record, h)
            summary.update(
                {
                    "configuration": cfg,
                    "supported_instruments": {
                        "symbols": cfg.get("symbols", []),
                        "exchanges": cfg.get("exchanges", []),
                        "timeframes": cfg.get("timeframes", []),
                    },
                    "available_transitions": [
                        s.value for s in allowed_transitions(StrategyStatus(record.status))
                    ],
                    "is_terminal": is_terminal(StrategyStatus(record.status)),
                    "is_editable": is_editable(StrategyStatus(record.status)),
                    "version_count": len(version_rows),
                    "versions": [_version_dict(v) for v in version_rows],
                }
            )
            return summary

    async def list_versions(self, strategy_id: str) -> list[dict]:
        async with self._db.session() as session:
            strategies = StrategyRepository(session)
            if await strategies.get_active(strategy_id) is None:
                raise StrategyNotFound(strategy_id)
            versions = StrategyVersionRepository(session)
            return [_version_dict(v) for v in await versions.list_for(strategy_id)]

    async def compare_versions(self, strategy_id: str, a: int, b: int) -> dict:
        async with self._db.session() as session:
            versions = StrategyVersionRepository(session)
            va = await versions.get_version(strategy_id, a)
            vb = await versions.get_version(strategy_id, b)
            if va is None or vb is None:
                raise StrategyNotFound(f"{strategy_id} versions {a}/{b}")
            return {
                "strategy_id": strategy_id,
                "a": _version_dict(va),
                "b": _version_dict(vb),
                "changed_fields": _diff_fields(va, vb),
            }

    async def get_audit(self, strategy_id: str) -> list[dict]:
        async with self._db.session() as session:
            strategies = StrategyRepository(session)
            if await strategies.get_active(strategy_id) is None:
                raise StrategyNotFound(strategy_id)
            audit = StrategyAuditRepository(session)
            return [_audit_dict(a) for a in await audit.list_for(strategy_id)]


class StrategyDashboardService:
    """Read-model for the strategy dashboard. Aggregates counts, health, recent activity."""

    def __init__(self, database: Database) -> None:
        self._db = database

    async def summary(self) -> dict:
        async with self._db.session() as session:
            strategies = StrategyRepository(session)
            health = StrategyHealthRepository(session)
            by_status = await strategies.count_by_status()
            all_rows = await strategies.list_filtered()
            recent = await strategies.recent(limit=6)

            scores = []
            trading_allowed = 0
            enabled = 0
            for r in all_rows:
                h = await health.get_for(r.id)
                if h is None:
                    continue
                if h.health_score is not None:
                    scores.append(h.health_score)
                trading_allowed += int(h.trading_allowed)
                enabled += int(h.enabled)

            avg_health = round(sum(scores) / len(scores), 4) if scores else None
            return {
                "total": len(all_rows),
                "by_status": by_status,
                "active": by_status.get(StrategyStatus.LIVE.value, 0),
                "draft": by_status.get(StrategyStatus.DRAFT.value, 0),
                "paused": by_status.get(StrategyStatus.PAUSED.value, 0),
                "health": {
                    "avg_score": avg_health,
                    "scored": len(scores),
                    "trading_allowed": trading_allowed,
                    "enabled": enabled,
                },
                "recent": [_summary_dict(r, None) for r in recent],
            }


# ---- module-level helpers ----------------------------------------------


def _clean_tags(tags: list[str] | None) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for t in tags or []:
        key = str(t).strip()
        if key and key.lower() not in seen:
            seen.add(key.lower())
            out.append(key)
    return out


def _new_version_record(
    strategy_id: str,
    version: int,
    name: str,
    description: str,
    category: str,
    tags: list[str],
    config: StrategyConfig,
    change_summary: str,
    actor: str,
    at: datetime,
) -> StrategyVersionRecord:
    return StrategyVersionRecord(
        id=_uuid(), strategy_id=strategy_id, version=version, name=name,
        description=description, category=category, tags=tags,
        config=config.model_dump(), change_summary=change_summary,
        created_by=actor, created_at=at,
    )


async def _record_audit(
    repo: StrategyAuditRepository,
    strategy_id: str,
    *,
    action: str,
    to_status: str | None = None,
    from_status: str | None = None,
    version: int | None = None,
    actor: str = "unknown",
    detail: str = "",
    at: datetime,
) -> None:
    await repo.add(
        StrategyAuditRecord(
            strategy_id=strategy_id, action=action, from_status=from_status,
            to_status=to_status, version=version, detail=detail, actor=actor, created_at=at,
        )
    )


def _summary_dict(r: StrategyRecord, h: StrategyHealthRecord | None) -> dict:
    return {
        "id": r.id,
        "name": r.name,
        "description": r.description,
        "category": r.category,
        "owner": r.owner,
        "status": r.status,
        "tags": list(r.tags or []),
        "version": r.current_version,
        "created_at": _iso(r.created_at),
        "updated_at": _iso(r.updated_at),
        "health": _health_dict(h),
    }


def _health_dict(h: StrategyHealthRecord | None) -> dict | None:
    if h is None:
        return None
    return {
        "health_score": h.health_score,
        "last_evaluation": _iso(h.last_evaluation),
        "last_execution": _iso(h.last_execution),
        "consecutive_failures": h.consecutive_failures,
        "consecutive_successes": h.consecutive_successes,
        "enabled": h.enabled,
        "trading_allowed": h.trading_allowed,
        "updated_at": _iso(h.updated_at),
    }


def _version_dict(v: StrategyVersionRecord) -> dict:
    return {
        "id": v.id,
        "version": v.version,
        "name": v.name,
        "description": v.description,
        "category": v.category,
        "tags": list(v.tags or []),
        "config": v.config,
        "change_summary": v.change_summary,
        "created_by": v.created_by,
        "created_at": _iso(v.created_at),
    }


def _audit_dict(a: StrategyAuditRecord) -> dict:
    return {
        "id": a.id,
        "action": a.action,
        "from_status": a.from_status,
        "to_status": a.to_status,
        "version": a.version,
        "detail": a.detail,
        "actor": a.actor,
        "created_at": _iso(a.created_at),
    }


def _diff_fields(a: StrategyVersionRecord, b: StrategyVersionRecord) -> list[str]:
    changed: list[str] = []
    for field in ("name", "description", "category"):
        if getattr(a, field) != getattr(b, field):
            changed.append(field)
    if list(a.tags or []) != list(b.tags or []):
        changed.append("tags")
    a_cfg, b_cfg = a.config or {}, b.config or {}
    for key in sorted(set(a_cfg) | set(b_cfg)):
        if a_cfg.get(key) != b_cfg.get(key):
            changed.append(f"config.{key}")
    return changed
