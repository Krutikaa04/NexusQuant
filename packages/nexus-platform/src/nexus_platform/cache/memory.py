"""In-memory cache with per-key TTL. Used in tests and single-process development."""

from __future__ import annotations

import time
from dataclasses import dataclass

from nexus_platform.cache.base import AbstractCache


@dataclass
class _Entry:
    value: str
    expires_at: float | None


class InMemoryCache(AbstractCache):
    def __init__(self) -> None:
        self._store: dict[str, _Entry] = {}

    def _live(self, key: str) -> _Entry | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        if entry.expires_at is not None and entry.expires_at < time.monotonic():
            self._store.pop(key, None)
            return None
        return entry

    async def get(self, key: str) -> str | None:
        entry = self._live(key)
        return entry.value if entry else None

    async def set(self, key: str, value: str, ttl: int | None = None) -> None:
        expires_at = time.monotonic() + ttl if ttl else None
        self._store[key] = _Entry(value=value, expires_at=expires_at)

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)

    async def clear_prefix(self, prefix: str) -> None:
        for key in [k for k in self._store if k.startswith(prefix)]:
            self._store.pop(key, None)
