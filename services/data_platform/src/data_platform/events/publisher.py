"""Outbound event publishing for the Data Platform.

The publisher port and its adapters now live in the domain kernel so every context shares
one implementation; this module re-exports them for local import stability.
"""

from __future__ import annotations

from nexus_shared.events.publisher import (
    EventPublisher,
    HttpFabricPublisher,
    InMemoryEventPublisher,
)

__all__ = ["EventPublisher", "HttpFabricPublisher", "InMemoryEventPublisher"]
