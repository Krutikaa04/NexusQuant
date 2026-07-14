"""In-process subscription registry and router (SPEC-005 §2 event routing).

Consumers register interest either in a specific :class:`EventType` or in a whole
:class:`EventCategory`. On publish, the router fans an envelope out to every matching
handler. Handlers are expected to be **idempotent** (SPEC-005 §5): the fabric guarantees
at-least-once delivery, so a handler may observe the same event more than once.

This is deliberately an in-process bus. It is the seam behind which a distributed
transport (Redis streams / a broker) can later be substituted without any consumer
change, because consumers only ever see the ``Handler`` contract.
"""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

from nexus_shared.events.catalog import EventCategory, EventType
from nexus_shared.events.envelope import EventEnvelope

logger = logging.getLogger(__name__)

Handler = Callable[[EventEnvelope], Awaitable[None]]


@dataclass
class Subscription:
    consumer_name: str
    handler: Handler
    event_types: frozenset[EventType] | None = None
    categories: frozenset[EventCategory] | None = None

    def matches(self, envelope: EventEnvelope) -> bool:
        if self.event_types is not None and envelope.event_type in self.event_types:
            return True
        if self.categories is not None and envelope.category in self.categories:
            return True
        return False


@dataclass
class SubscriptionRegistry:
    """Holds active subscriptions and dispatches envelopes to matching handlers."""

    _subs: list[Subscription] = field(default_factory=list)
    _delivered: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    _failed: dict[str, int] = field(default_factory=lambda: defaultdict(int))

    def subscribe(
        self,
        consumer_name: str,
        handler: Handler,
        *,
        event_types: list[EventType] | None = None,
        categories: list[EventCategory] | None = None,
    ) -> Subscription:
        if not event_types and not categories:
            raise ValueError("a subscription must target at least one type or category")
        sub = Subscription(
            consumer_name=consumer_name,
            handler=handler,
            event_types=frozenset(event_types) if event_types else None,
            categories=frozenset(categories) if categories else None,
        )
        self._subs.append(sub)
        logger.info("consumer '%s' subscribed", consumer_name)
        return sub

    def unsubscribe(self, subscription: Subscription) -> None:
        self._subs = [s for s in self._subs if s is not subscription]

    async def dispatch(self, envelope: EventEnvelope) -> None:
        """Deliver ``envelope`` to all matching handlers concurrently.

        A failing handler is isolated: its exception is logged and counted but does not
        prevent delivery to other consumers (at-least-once, per-consumer independence).
        """
        matching = [s for s in self._subs if s.matches(envelope)]
        if not matching:
            return
        results = await asyncio.gather(
            *(self._deliver(s, envelope) for s in matching), return_exceptions=True
        )
        for sub, result in zip(matching, results):
            if isinstance(result, Exception):
                self._failed[sub.consumer_name] += 1
                logger.exception(
                    "consumer '%s' failed handling %s",
                    sub.consumer_name,
                    envelope.event_type.value,
                    exc_info=result,
                )
            else:
                self._delivered[sub.consumer_name] += 1

    async def _deliver(self, sub: Subscription, envelope: EventEnvelope) -> None:
        await sub.handler(envelope)

    @property
    def consumer_count(self) -> int:
        return len(self._subs)

    def stats(self) -> dict[str, dict[str, int]]:
        names = {s.consumer_name for s in self._subs}
        return {
            name: {
                "delivered": self._delivered.get(name, 0),
                "failed": self._failed.get(name, 0),
            }
            for name in names
        }
