"""The cache port (SPEC-006 §3 Redis cache).

Services depend on this ``Cache`` protocol, not on Redis directly, so an in-memory cache
can be substituted in tests and a Redis cache in production without any call-site change.
Values are JSON — the ``*_json`` helpers on :class:`AbstractCache` handle (de)serialisation.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Cache(Protocol):
    async def get(self, key: str) -> str | None: ...
    async def set(self, key: str, value: str, ttl: int | None = None) -> None: ...
    async def delete(self, key: str) -> None: ...
    async def clear_prefix(self, prefix: str) -> None: ...


class AbstractCache(ABC):
    """Base with JSON convenience helpers on top of the raw string cache contract."""

    @abstractmethod
    async def get(self, key: str) -> str | None: ...

    @abstractmethod
    async def set(self, key: str, value: str, ttl: int | None = None) -> None: ...

    @abstractmethod
    async def delete(self, key: str) -> None: ...

    @abstractmethod
    async def clear_prefix(self, prefix: str) -> None:
        """Invalidate every key beginning with ``prefix`` (read-model invalidation)."""

    async def get_json(self, key: str) -> Any | None:
        raw = await self.get(key)
        return None if raw is None else json.loads(raw)

    async def set_json(self, key: str, value: Any, ttl: int | None = None) -> None:
        await self.set(key, json.dumps(value, default=str), ttl)
