"""NexusQuant technical infrastructure kernel.

Domain-agnostic plumbing shared by every service: async database session management, a
generic repository base, a cache abstraction, and a reproducible migration runner. Unlike
:mod:`nexus_shared` (which holds *domain contracts*), this package holds *technical
primitives* only — no event types, no business shapes.
"""

from nexus_platform.cache.base import Cache
from nexus_platform.cache.memory import InMemoryCache
from nexus_platform.db.repository import BaseRepository
from nexus_platform.db.session import Database
from nexus_platform.migrations.runner import Migration, MigrationRunner

__all__ = [
    "Cache",
    "InMemoryCache",
    "BaseRepository",
    "Database",
    "Migration",
    "MigrationRunner",
]
