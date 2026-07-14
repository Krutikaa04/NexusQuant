"""In-memory cache tests: get/set, JSON helpers, prefix invalidation, TTL expiry."""

from __future__ import annotations

import time

from nexus_platform.cache.memory import InMemoryCache


async def test_set_and_get() -> None:
    cache = InMemoryCache()
    await cache.set("k", "v")
    assert await cache.get("k") == "v"
    assert await cache.get("missing") is None


async def test_json_roundtrip() -> None:
    cache = InMemoryCache()
    await cache.set_json("obj", {"a": 1, "b": [1, 2]})
    assert await cache.get_json("obj") == {"a": 1, "b": [1, 2]}


async def test_delete_and_prefix_invalidation() -> None:
    cache = InMemoryCache()
    await cache.set("datasets:1", "a")
    await cache.set("datasets:2", "b")
    await cache.set("features:1", "c")
    await cache.clear_prefix("datasets:")
    assert await cache.get("datasets:1") is None
    assert await cache.get("datasets:2") is None
    assert await cache.get("features:1") == "c"


async def test_ttl_expiry(monkeypatch) -> None:
    cache = InMemoryCache()
    base = time.monotonic()
    monkeypatch.setattr("nexus_platform.cache.memory.time.monotonic", lambda: base)
    await cache.set("k", "v", ttl=10)
    assert await cache.get("k") == "v"
    monkeypatch.setattr("nexus_platform.cache.memory.time.monotonic", lambda: base + 11)
    assert await cache.get("k") is None
