"""WebSocket connection manager and fan-out (SPEC-005 §6).

Maintains one set of live connections per channel. When the Publisher persists an event it
calls :meth:`broadcast`, which serialises the envelope once and pushes it to every socket
subscribed to the event's channel. Channels map one-to-one onto event categories.

The gateway is a :class:`StreamSink`, so the Publisher depends only on that interface and
never on WebSocket details.
"""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict

from fastapi import WebSocket
from nexus_shared.events.catalog import EventCategory
from nexus_shared.events.envelope import EventEnvelope
from event_fabric.services.publisher import StreamSink

logger = logging.getLogger(__name__)

# SPEC-005 §6 channels. Each maps to the event categories it carries.
CHANNELS: dict[str, frozenset[EventCategory]] = {
    "market": frozenset({EventCategory.MARKET}),
    "research": frozenset({EventCategory.RESEARCH, EventCategory.ALPHA}),
    "portfolio": frozenset({EventCategory.PORTFOLIO, EventCategory.DECISION}),
    "orders": frozenset({EventCategory.EXECUTION}),
    "governance": frozenset({EventCategory.GOVERNANCE}),
    "system": frozenset({EventCategory.SYSTEM}),
}


def _channel_for(category: EventCategory) -> str | None:
    for channel, categories in CHANNELS.items():
        if category in categories:
            return channel
    return None


class WebSocketGateway(StreamSink):
    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, channel: str, websocket: WebSocket) -> None:
        if channel not in CHANNELS:
            raise ValueError(f"unknown channel '{channel}'")
        await websocket.accept()
        async with self._lock:
            self._connections[channel].add(websocket)
        logger.info("ws connected to '%s' (%d live)", channel, len(self._connections[channel]))

    async def disconnect(self, channel: str, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections[channel].discard(websocket)

    async def broadcast(self, envelope: EventEnvelope) -> None:
        channel = _channel_for(envelope.category)
        if channel is None:
            return
        message = envelope.model_dump(mode="json")
        async with self._lock:
            targets = list(self._connections[channel])
        dead: list[WebSocket] = []
        for ws in targets:
            try:
                await ws.send_json(message)
            except Exception:  # connection dropped mid-send
                dead.append(ws)
        if dead:
            async with self._lock:
                for ws in dead:
                    self._connections[channel].discard(ws)

    def connection_count(self) -> int:
        return sum(len(conns) for conns in self._connections.values())
