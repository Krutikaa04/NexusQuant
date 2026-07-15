"""REST + WebSocket routes for Market Intelligence (SPEC-004 Public APIs).

Thin routes over the injected services. The development-mode synthetic feed is exposed via
``POST /market/ingest/mock`` — the explicit mock ingestion path (SPEC-001: never fake data
unless explicitly in mock development mode).
"""

from __future__ import annotations

from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket, WebSocketDisconnect
from starlette import status

from market_intelligence.api.dto import (
    CorporateActionBody,
    HealthResponse,
    HolidayBody,
    IngestResultResponse,
    InstrumentBody,
    InstrumentUpsertResponse,
    MockIngestBody,
    ReplayResponse,
)
from market_intelligence.container import Container
from market_intelligence.domain.calendar import IST, Holiday
from market_intelligence.domain.candles import Interval
from market_intelligence.domain.instruments import Exchange, Segment
from market_intelligence.ingestion.vendor import MockNseVendor
from market_intelligence.security import Principal, require_principal

router = APIRouter(prefix="/market", tags=["market-intelligence"])


def get_container(request: Request) -> Container:
    return request.app.state.container


@router.get("/health", response_model=HealthResponse)
async def health(container: Container = Depends(get_container)) -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=container.settings.service_name,
        environment=container.settings.environment,
        migrations_applied=container.applied_migrations,
    )


# --- Instrument Master ---


@router.get("/instruments")
async def list_instruments(
    segment: Segment | None = None,
    exchange: Exchange | None = None,
    container: Container = Depends(get_container),
) -> list[dict]:
    instruments = await container.instruments.list(segment=segment, exchange=exchange)
    return [
        {
            "symbol": i.symbol,
            "exchange": i.exchange.value,
            "name": i.name,
            "segment": i.segment.value,
            "isin": i.isin,
            "tick_size": i.tick_size,
            "lot_size": i.lot_size,
            "sector": i.sector,
            "industry": i.industry,
            "currency": i.currency,
            "listing_status": i.listing_status.value,
        }
        for i in instruments
    ]


@router.put(
    "/instruments",
    response_model=InstrumentUpsertResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upsert_instrument(
    body: InstrumentBody,
    container: Container = Depends(get_container),
    principal: Principal = Depends(require_principal),
) -> InstrumentUpsertResponse:
    revision = await container.instruments.upsert(body.to_domain())
    return InstrumentUpsertResponse(
        symbol=body.symbol, exchange=body.exchange, revision=revision
    )


# --- Market data reads (SPEC-004 Public APIs) ---


@router.get("/ticks")
async def get_ticks(
    symbol: str,
    since: datetime | None = None,
    limit: int = 500,
    container: Container = Depends(get_container),
) -> list[dict]:
    return await container.queries.ticks(symbol, since=since, limit=min(limit, 5000))


@router.get("/candles")
async def get_candles(
    symbol: str,
    interval_seconds: int = 60,
    since: datetime | None = None,
    limit: int = 500,
    container: Container = Depends(get_container),
) -> list[dict]:
    try:
        interval = Interval(interval_seconds)
    except ValueError:
        valid = ", ".join(str(int(i)) for i in Interval)
        raise HTTPException(
            422,
            detail=f"unsupported interval; valid values (seconds): {valid}",
        )
    return await container.queries.candles(symbol, interval, since=since, limit=min(limit, 5000))


@router.get("/quality")
async def get_quality(
    symbol: str, container: Container = Depends(get_container)
) -> dict:
    snapshot = await container.queries.quality(symbol)
    if snapshot is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"no quality data for '{symbol}'")
    return snapshot


# --- Ingestion (development mock mode) and replay ---


@router.post(
    "/ingest/mock",
    response_model=IngestResultResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def ingest_mock(
    body: MockIngestBody,
    container: Container = Depends(get_container),
    principal: Principal = Depends(require_principal),
) -> IngestResultResponse:
    """Run the deterministic synthetic feed through the full ingestion pipeline."""
    # Symbols must exist in the Instrument Master first (symbol validation).
    unknown = [
        s
        for s in body.symbols
        if await container.instruments.get(s, body.exchange) is None
    ]
    if unknown:
        raise HTTPException(
            422,
            detail=f"symbols not in instrument master: {', '.join(sorted(unknown))}",
        )
    vendor = MockNseVendor(body.symbols, exchange=body.exchange.value, seed=body.seed)
    result = await container.pipeline.process_batch(list(vendor.stream(body.count)))
    return IngestResultResponse(
        accepted=result.accepted,
        rejected=result.rejected,
        candles_closed=result.candles_closed,
        quality_changes=result.quality_changes,
        events_published=result.events_published,
        rejections=result.rejections,
    )


@router.post("/replay", response_model=ReplayResponse)
async def replay(
    symbol: str,
    since: datetime | None = None,
    limit: int = 1000,
    publish: bool = False,
    container: Container = Depends(get_container),
    principal: Principal = Depends(require_principal),
) -> ReplayResponse:
    report = await container.replay.replay_ticks(
        symbol, since=since, limit=min(limit, 10_000), publish=publish
    )
    return ReplayResponse(
        symbol=report.symbol, replayed=report.replayed, published=report.published
    )


# --- Calendar, corporate actions, regime (SPEC-004 subsystems) ---


@router.get("/calendar")
async def calendar_info(
    day: date | None = None,
    container: Container = Depends(get_container),
) -> dict:
    cal = await container.calendar.load()
    target = day or datetime.now(IST).date()
    window = cal.session_window(target)
    return {
        "day": target.isoformat(),
        "is_trading_day": cal.is_trading_day(target),
        "is_holiday": cal.is_holiday(target),
        "session_open": window[0].isoformat() if window else None,
        "session_close": window[1].isoformat() if window else None,
        "next_trading_day": cal.next_trading_day(target).isoformat(),
        "weekly_expiry": cal.weekly_expiry(target).isoformat(),
        "monthly_expiry": cal.monthly_expiry(target.year, target.month).isoformat(),
    }


@router.put("/calendar/holidays", status_code=status.HTTP_201_CREATED)
async def add_holiday(
    body: HolidayBody,
    container: Container = Depends(get_container),
    principal: Principal = Depends(require_principal),
) -> dict:
    await container.calendar.add_holiday(Holiday(day=body.day, reason=body.reason))
    return {"day": body.day.isoformat(), "reason": body.reason}


@router.get("/corporate-actions")
async def list_corporate_actions(
    symbol: str,
    exchange: Exchange = Exchange.NSE,
    container: Container = Depends(get_container),
) -> list[dict]:
    actions = await container.corporate_actions.list_for(symbol, exchange.value)
    return [
        {
            "symbol": a.symbol,
            "exchange": a.exchange,
            "action_type": a.action_type.value,
            "ex_date": a.ex_date.isoformat(),
            "details": a.details,
        }
        for a in actions
    ]


@router.post("/corporate-actions", status_code=status.HTTP_201_CREATED)
async def record_corporate_action(
    body: CorporateActionBody,
    container: Container = Depends(get_container),
    principal: Principal = Depends(require_principal),
) -> dict:
    version = await container.corporate_actions.record(body.to_domain())
    return {"symbol": body.symbol, "adjustment_version": version}


@router.get("/candles/adjusted")
async def get_adjusted_candles(
    symbol: str,
    exchange: Exchange = Exchange.NSE,
    interval_seconds: int = 60,
    since: datetime | None = None,
    limit: int = 500,
    up_to_version: int | None = None,
    container: Container = Depends(get_container),
) -> list[dict]:
    try:
        interval = Interval(interval_seconds)
    except ValueError:
        raise HTTPException(422, detail="unsupported interval")
    return await container.corporate_actions.adjusted_candles(
        symbol, exchange.value, interval,
        since=since, limit=min(limit, 5000), up_to_version=up_to_version,
    )


@router.get("/regime")
async def get_regime(
    symbol: str, container: Container = Depends(get_container)
) -> dict:
    current = await container.regime.current(symbol)
    if current is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"no regime data for '{symbol}'")
    return current


@router.post("/regime/assess")
async def assess_regime(
    symbol: str,
    container: Container = Depends(get_container),
    principal: Principal = Depends(require_principal),
) -> dict:
    result = await container.regime.assess(symbol, as_of=datetime.now(IST))
    if result is None:
        raise HTTPException(
            422, detail=f"insufficient candle history for '{symbol}' to classify a regime"
        )
    return result


# --- WebSocket streams (SPEC-004 WebSockets) ---

ws_router = APIRouter(tags=["market-intelligence-ws"])


@ws_router.websocket("/ws/{channel}")
async def stream(websocket: WebSocket, channel: str) -> None:
    container: Container = websocket.app.state.container
    from market_intelligence.ws.gateway import CHANNELS

    if channel not in CHANNELS:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    await container.gateway.connect(channel, websocket)
    try:
        while True:
            await websocket.receive_text()  # detect disconnects / heartbeats
    except WebSocketDisconnect:
        await container.gateway.disconnect(channel, websocket)
