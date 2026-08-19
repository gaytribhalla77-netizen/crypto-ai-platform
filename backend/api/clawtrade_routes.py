from fastapi import APIRouter, Depends, HTTPException, Query

from auth.dependencies import CurrentUser, get_current_user
from clawtrade.client import ClawtradeClient, ClawtradeError
from core.config import settings

router = APIRouter(prefix="/api/clawtrade", tags=["clawtrade"])


def _client() -> ClawtradeClient:
    return ClawtradeClient()


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


@router.get("/market/price")
async def market_price(symbol: str = Query(..., min_length=3, max_length=30), exchange: str = "binance",
                       user: CurrentUser = Depends(get_current_user)):
    if not settings.clawtrade_enabled:
        raise HTTPException(503, "Clawtrade integration is disabled")
    try:
        return await _client().price(symbol, exchange)
    except ClawtradeError as exc:
        raise HTTPException(502, str(exc)) from exc


@router.get("/market/candles")
async def market_candles(symbol: str = Query(..., min_length=3, max_length=30), timeframe: str = "1h",
                         limit: int = Query(100, ge=1, le=1000), exchange: str = "binance",
                         user: CurrentUser = Depends(get_current_user)):
    if not settings.clawtrade_enabled:
        raise HTTPException(503, "Clawtrade integration is disabled")
    try:
        return await _client().candles(symbol, timeframe, limit, exchange)
    except ClawtradeError as exc:
        raise HTTPException(502, str(exc)) from exc


@router.get("/market/orderbook")
async def market_orderbook(symbol: str = Query(..., min_length=3, max_length=30), depth: int = Query(20, ge=1, le=100),
                           exchange: str = "binance", user: CurrentUser = Depends(get_current_user)):
    if not settings.clawtrade_enabled:
        raise HTTPException(503, "Clawtrade integration is disabled")
    try:
        return await _client().orderbook(symbol, depth, exchange)
    except ClawtradeError as exc:
        raise HTTPException(502, str(exc)) from exc
