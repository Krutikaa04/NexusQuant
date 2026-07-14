"""Central definition of cache key layout so writers and readers stay in agreement."""

from __future__ import annotations

from data_platform.domain import ArtifactKind

_PREFIX = "dp:artifacts"


def kind_prefix(kind: ArtifactKind) -> str:
    """Prefix covering every cached entry for a kind — used to invalidate on write."""
    return f"{_PREFIX}:{kind.value}:"


def list_key(kind: ArtifactKind) -> str:
    return f"{_PREFIX}:{kind.value}:__list__"


def item_key(kind: ArtifactKind, namespace: str, name: str) -> str:
    return f"{_PREFIX}:{kind.value}:{namespace}:{name}"


def read_model_key(kind: ArtifactKind, namespace: str, name: str) -> str:
    """Durable read-model key (persisted in ``read_models``, not just cached)."""
    return f"{kind.value}:{namespace}:{name}"
