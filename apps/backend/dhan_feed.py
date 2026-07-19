"""Live market-data feed backed by the DhanHQ v2 REST API (real NSE data).

This is the production-path counterpart to the synthetic ``LiveFeed`` in seed.py. It polls
Dhan's ``/v2/marketfeed/quote`` endpoint and pushes real quotes through the *same*
validate → normalize → quality → candle pipeline — no downstream code changes.

Honesty guarantees (per the market-data mandate):
* It ingests only while NSE is in its OPEN continuous session (checked against the real
  trading calendar). Outside market hours it does not push ticks, so last-close values are
  never restamped as fresh, live data.
* Credentials are read from the environment; they are never logged. If they are absent the
  BFF uses the synthetic feed instead — this class is only constructed when a token is set.
* Symbols that cannot be resolved in the security master are logged explicitly, never
  silently dropped.

The trader must supply their own free Dhan API credentials (DHAN_CLIENT_ID,
DHAN_ACCESS_TOKEN). This code never performs the broker login/authentication itself.
"""

from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import httpx
from sqlalchemy import func, select

from market_intelligence.container import Container
from market_intelligence.db.models import TickRecord
from market_intelligence.domain.calendar import IST, SessionPhase
from market_intelligence.ingestion.dhan import (
    DHAN_QUOTE_URL,
    DHAN_SCRIP_MASTER_URL,
    DhanInstrument,
    quote_response_to_ticks,
    request_groups,
    resolve_security_ids,
)

logger = logging.getLogger("nexus.backend.dhan")

_MASTER_CACHE = Path(".dev/dhan_scrip_master.csv")


@dataclass(frozen=True, slots=True)
class DhanConfig:
    client_id: str
    access_token: str
    interval_s: float = 2.0  # Dhan quote rate limit is 1 req/sec; 2s is comfortable.

    @classmethod
    def from_env(cls) -> "DhanConfig | None":
        client_id = os.environ.get("DHAN_CLIENT_ID", "").strip()
        token = os.environ.get("DHAN_ACCESS_TOKEN", "").strip()
        if not client_id or not token:
            return None
        return cls(client_id=client_id, access_token=token)


async def _load_security_master(client: httpx.AsyncClient) -> str:
    """Return the security-master CSV text, caching it locally for the day."""
    if _MASTER_CACHE.exists():
        return _MASTER_CACHE.read_text(encoding="utf-8", errors="replace")
    logger.info("downloading Dhan security master…")
    resp = await client.get(DHAN_SCRIP_MASTER_URL, timeout=60)
    resp.raise_for_status()
    _MASTER_CACHE.parent.mkdir(parents=True, exist_ok=True)
    _MASTER_CACHE.write_text(resp.text, encoding="utf-8")
    return resp.text


class DhanMarketFeed:
    def __init__(self, container: Container, config: DhanConfig) -> None:
        self._container = container
        self._config = config
        self._task: asyncio.Task | None = None
        self._client: httpx.AsyncClient | None = None
        self._by_key: dict[tuple[str, str], DhanInstrument] = {}
        self._groups: dict[str, list[int]] = {}
        self._sequences: dict[str, int] = {}

    @property
    def headers(self) -> dict[str, str]:
        return {
            "access-token": self._config.access_token,
            "client-id": self._config.client_id,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def start(self) -> None:
        self._client = httpx.AsyncClient()
        csv_text = await _load_security_master(self._client)
        self._by_key, unresolved = resolve_security_ids(csv_text)
        self._groups = request_groups(self._by_key)
        if unresolved:
            logger.warning(
                "Dhan: %d symbol(s) unresolved in security master (skipped): %s",
                len(unresolved), ", ".join(unresolved),
            )
        if not self._by_key:
            logger.error("Dhan: no instruments resolved; feed will not start")
            return
        await self._seed_sequences()
        self._task = asyncio.create_task(self._run(), name="nexus-dhan-feed")
        logger.info("Dhan live feed started (%d instruments)", len(self._by_key))

    async def _seed_sequences(self) -> None:
        """Continue each symbol's tick sequence from stored history so it stays monotonic."""
        symbols = {inst.symbol for inst in self._by_key.values()}
        async with self._container.database.session() as session:
            for symbol in symbols:
                mx = (
                    await session.execute(
                        select(func.max(TickRecord.sequence)).where(TickRecord.symbol == symbol)
                    )
                ).scalar_one_or_none()
                self._sequences[symbol] = mx or 0

    async def _is_open(self) -> bool:
        now = datetime.now(IST)
        calendar = await self._container.calendar.load()
        return calendar.is_trading_day(now.date()) and calendar.phase_at(now) is SessionPhase.OPEN

    async def _poll_once(self) -> None:
        assert self._client is not None
        resp = await self._client.post(
            DHAN_QUOTE_URL, headers=self.headers, json=self._groups, timeout=10
        )
        resp.raise_for_status()
        payload = resp.json()
        ticks = quote_response_to_ticks(
            payload, self._by_key, sequences=self._sequences, now=datetime.now(IST)
        )
        if ticks:
            await self._container.pipeline.process_batch(ticks)

    async def _run(self) -> None:
        closed_logged = False
        while True:
            await asyncio.sleep(self._config.interval_s)
            try:
                if not await self._is_open():
                    if not closed_logged:
                        logger.info("Dhan: NSE closed — not ingesting (last values retained)")
                        closed_logged = True
                    continue
                closed_logged = False
                await self._poll_once()
            except asyncio.CancelledError:
                raise
            except httpx.HTTPStatusError as exc:
                logger.error("Dhan quote request failed: %s (check token/credentials)", exc)
            except Exception:
                logger.exception("Dhan feed cycle failed; continuing")

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if self._client is not None:
            await self._client.aclose()
