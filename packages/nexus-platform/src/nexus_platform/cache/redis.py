"""Redis-backed cache (SPEC-006 §3). Imported lazily so ``redis`` is an optional dependency."""

from __future__ import annotations

from nexus_platform.cache.base import AbstractCache


class RedisCache(AbstractCache):
    """Async Redis cache. ``clear_prefix`` scans with ``MATCH`` to avoid blocking KEYS."""

    def __init__(self, url: str) -> None:
        import redis.asyncio as redis  # local import keeps redis optional

        self._redis = redis.from_url(url, decode_responses=True)

    async def get(self, key: str) -> str | None:
        return await self._redis.get(key)

    async def set(self, key: str, value: str, ttl: int | None = None) -> None:
        await self._redis.set(key, value, ex=ttl)

    async def delete(self, key: str) -> None:
        await self._redis.delete(key)

    async def clear_prefix(self, prefix: str) -> None:
        async for key in self._redis.scan_iter(match=f"{prefix}*"):
            await self._redis.delete(key)

    async def close(self) -> None:
        await self._redis.aclose()
