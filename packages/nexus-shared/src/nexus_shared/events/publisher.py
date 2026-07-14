"""Outbound event-publishing port and adapters (SPEC-005 boundary rule).

A bounded context never writes into another context's database, nor into the Event
Fabric's store — it *publishes* through the fabric's public REST ingress. Call sites depend
on the :class:`EventPublisher` port; the HTTP adapter is used in production and the
in-memory adapter in tests and offline development.

This lives in the domain kernel (``nexus_shared``) because every context that emits events
needs it; the HTTP adapter imports ``httpx`` lazily so it stays an optional dependency.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from nexus_shared.events.catalog import EventType
from nexus_shared.events.envelope import EventEnvelope


class EventPublisher(ABC):
    @abstractmethod
    async def publish(self, envelope: EventEnvelope) -> None: ...

    async def publish_all(self, envelopes: list[EventEnvelope]) -> None:
        for envelope in envelopes:
            await self.publish(envelope)


class InMemoryEventPublisher(EventPublisher):
    """Collects published envelopes in order. Used by tests and offline development."""

    def __init__(self) -> None:
        self.published: list[EventEnvelope] = []

    async def publish(self, envelope: EventEnvelope) -> None:
        self.published.append(envelope)

    def of_type(self, event_type: EventType) -> list[EventEnvelope]:
        return [e for e in self.published if e.event_type == event_type]


class HttpFabricPublisher(EventPublisher):
    """Publishes to the Event Fabric's ``POST /events`` ingress over HTTP."""

    def __init__(self, base_url: str, *, token: str | None = None, timeout: float = 5.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._headers = {"Authorization": f"Bearer {token}"} if token else {}
        self._timeout = timeout

    async def publish(self, envelope: EventEnvelope) -> None:
        import httpx  # lazy import keeps httpx optional for the kernel

        body = {
            "event_type": envelope.event_type.value,
            "event_version": envelope.event_version,
            "producer": envelope.producer,
            "correlation_id": str(envelope.correlation_id),
            "aggregate_id": envelope.aggregate_id,
            "payload": envelope.payload,
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(f"{self._base_url}/events", json=body, headers=self._headers)
            resp.raise_for_status()
