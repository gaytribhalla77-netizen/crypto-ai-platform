from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from auth.dependencies import CurrentUser, get_current_user
from clawtrade.client import ClawtradeClient, ClawtradeError
from core.config import settings

router = APIRouter(prefix="/api/clawtrade", tags=["clawtrade"])


def _client() -> ClawtradeClient:
    return ClawtradeClient(
        base_url=settings.clawtrade_base_url,
        timeout=settings.clawtrade_timeout_seconds,
    )


def _require_enabled() -> None:
    if not settings.clawtrade_enabled:
        raise HTTPException(503, "Clawtrade integration is disabled")


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=8000)


class BacktestRequest(BaseModel):
    symbol: str = Field(default="BTC/USDT", min_length=3, max_length=30)
    timeframe: str = Field(default="1d", min_length=1, max_length=10)
    days: int = Field(default=90, ge=1, le=3650)
    strategy: str = Field(default="momentum", min_length=1, max_length=100)
    capital: float = Field(default=10000, gt=0, le=10_000_000)
    exchange: str = Field(default="binance", min_length=1, max_length=30)


@router.get("/status")
async def status(user: CurrentUser = Depends(get_current_user)):
    """Return integration health; never enables trading."""
    if not settings.clawtrade_enabled:
        return {"enabled": False, "connected": False, "trading_authority": "platform_only"}
    try:
        health = await _client().health()
        return {"enabled": True, "connected": True, "trading_authority": "platform_only", "health": health}
    except ClawtradeError as exc:
        return {"enabled": True, "connected": False, "trading_authority": "platform_only", "error": str(exc)}


@router.post("/chat")
async def chat(payload: ChatRequest, user: CurrentUser = Depends(get_current_user)):
    """Ask the external Clawtrade agent for analysis; no order execution."""
    _require_enabled()
    try:
        return await _client().chat(payload.message)
    except ClawtradeError as exc:
        raise HTTPException(502, str(exc)) from exc


@router.get("/agents")
async def agents(user: CurrentUser = Depends(get_current_user)):
    _require_enabled()
    try:
        return await _client().agents()
    except ClawtradeError as exc:
        raise HTTPException(502, str(exc)) from exc


@router.get("/agents/events")
async def agent_events(limit: int = Query(50, ge=1, le=200), user: CurrentUser = Depends(get_current_user)):
    _require_enabled()
    try:
        return await _client().agent_events(limit)
    except ClawtradeError as exc:
        raise HTTPException(502, str(exc)) from exc


@router.post("/backtest")
async def backtest(payload: BacktestRequest, user: CurrentUser = Depends(get_current_user)):
    _require_enabled()
    try:
        return await _client().backtest(payload.model_dump())
    except ClawtradeError as exc:
        raise HTTPException(502, str(exc)) from exc


@router.get("/market/price")
async def market_price(symbol: str = Query(..., min_length=3, max_length=30), exchange: str = "binance",
                       user: CurrentUser = Depends(get_current_user)):
    _require_enabled()
    try:
        return await _client().price(symbol, exchange)
    except ClawtradeError as exc:
        raise HTTPException(502, str(exc)) from exc


@router.get("/market/candles")
async def market_candles(symbol: str = Query(..., min_length=3, max_length=30), timeframe: str = "1h",
                         limit: int = Query(100, ge=1, le=1000), exchange: str = "binance",
                         user: CurrentUser = Depends(get_current_user)):
    _require_enabled()
    try:
        return await _client().candles(symbol, timeframe, limit, exchange)
    except ClawtradeError as exc:
        raise HTTPException(502, str(exc)) from exc


@router.get("/market/orderbook")
async def market_orderbook(symbol: str = Query(..., min_length=3, max_length=30), depth: int = Query(20, ge=1, le=100),
                           exchange: str = "binance", user: CurrentUser = Depends(get_current_user)):
    _require_enabled()
    try:
        return await _client().orderbook(symbol, depth, exchange)
    except ClawtradeError as exc:
        raise HTTPException(502, str(exc)) from exc
