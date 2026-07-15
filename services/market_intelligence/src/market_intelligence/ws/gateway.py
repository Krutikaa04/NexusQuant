"""WebSocket gateway and a broadcasting publisher (SPEC-004 /ws/market, /ws/regime, /ws/calendar).

Market Intelligence exposes low-latency local streams for dashboards (SPEC-004 dashboard
propagation < 100 ms). The :class:`BroadcastPublisher` decorates the real event publisher:
every envelope still goes to the fabric, and is *also* fanned out to any connected sockets
whose channel matches the event. Consumers therefore see the identical published events with
no extra round-trip.
"""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from collections.abc import Callable

from fastapi import WebSocket

from nexus_shared.events.catalog import EventType
from nexus_shared.events.envelope import EventEnvelope
from nexus_shared.events.publisher import EventPublisher

logger = logging.getLogger(__name__)

# Channel -> predicate selecting which events it carries (SPEC-004 WebSockets).
CHANNELS: dict[str, Callable[[EventEnvelope], bool]] = {
    "market": lambda e: e.event_type
    in {EventType.TICK_RECEIVED, EventType.CANDLE_CLOSED, EventType.DATA_QUALITY_CHANGED},
    "regime": lambda e: e.event_type is EventType.MARKET_REGIME_CHANGED,
    "calendar": lambda e: e.event_type
    in {EventType.TRADING_SESSION_OPENED, EventType.TRADING_SESSION_CLOSED},
}


class WebSocketGateway:
    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, channel: str, websocket: WebSocket) -> None:
        if channel not in CHANNELS:
            raise ValueError(f"unknown channel '{channel}'")
        await websocket.accept()
        async with self._lock:
            self._connections[channel].add(websocket)

    async def disconnect(self, channel: str, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections[channel].discard(websocket)

    async def broadcast(self, envelope: EventEnvelope) -> None:
        message = envelope.model_dump(mode="json")
        for channel, predicate in CHANNELS.items():
            if not predicate(envelope):
                continue
            async with self._lock:
                targets = list(self._connections[channel])
            dead: list[WebSocket] = []
            for ws in targets:
                try:
                    await ws.send_json(message)
                except Exception:
                    dead.append(ws)
            if dead:
                async with self._lock:
                    for ws in dead:
                        self._connections[channel].discard(ws)

    def connection_count(self) -> int:
        return sum(len(conns) for conns in self._connections.values())


class BroadcastPublisher(EventPublisher):
    """Publisher decorator: forwards to the fabric and mirrors to local WebSocket clients."""

    def __init__(self, inner: EventPublisher, gateway: WebSocketGateway) -> None:
        self._inner = inner
        self._gateway = gateway

    async def publish(self, envelope: EventEnvelope) -> None:
        await self._inner.publish(envelope)
        try:
            await self._gateway.broadcast(envelope)
        except Exception:  # local streaming is best-effort; never block publishing
            logger.exception("ws broadcast failed for %s", envelope.event_id)
