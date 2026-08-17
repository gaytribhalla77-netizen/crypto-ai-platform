import asyncio

from fastapi import APIRouter, HTTPException, Depends

from auth.dependencies import get_current_user, get_db_session
from database.repository import TradeRepository, PositionRepository
from market.binance_public import ticker, klines
from news.engine import NewsEngine
from trading.position_monitor import PositionMonitor
from core.config import settings

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])
_news = NewsEngine()
_monitor = PositionMonitor()


@router.get("/history")
async def order_history(
    limit: int = 100,
    user=Depends(get_current_user),
    session=Depends(get_db_session),
):
    """Order history / journal — every trade this user has placed, newest
    first. Nothing new to compute: it was already being persisted to the
    trades table on every order attempt (database/models.Trade); this just
    exposes it."""
    trades = await TradeRepository(session).list_by_user(user.id, limit=limit)
    return {
        "count": len(trades),
        "trades": [
            {
                "id": t.id,
                "symbol": t.symbol,
                "side": t.side,
                "amount_usdt": t.amount_usdt,
                "status": t.status,
                "exchange_order_id": t.exchange_order_id,
                "created_at": t.created_at.isoformat() if t.created_at else None,
                "updated_at": t.updated_at.isoformat() if t.updated_at else None,
            }
            for t in trades
        ],
    }


@router.get("/positions")
async def open_positions(
    user=Depends(get_current_user),
    session=Depends(get_db_session),
):
    """Open positions with a live stop-loss/take-profit evaluation against
    the current market price — the same logic the background
    position-monitor worker uses, just on-demand for this one user."""
    repo = PositionRepository(session)
    positions = await repo.open_positions(user.id)
    out = []
    for p in positions:
        try:
            data = await ticker(p.symbol)
            current = float(data["lastPrice"])
            evaluation = _monitor.evaluate(p.side, p.entry_price, current, p.stop_loss_price, p.take_profit_price)
        except Exception:
            current = None
            evaluation = None
        out.append({
            "id": p.id, "symbol": p.symbol, "side": p.side,
            "quantity": p.quantity, "entry_price": p.entry_price,
            "stop_loss_price": p.stop_loss_price, "take_profit_price": p.take_profit_price,
            "current_price": current, "evaluation": evaluation,
        })
    return {"count": len(out), "positions": out}


@router.get("/portfolio")
async def portfolio_summary(
    user=Depends(get_current_user),
    session=Depends(get_db_session),
):
    """Aggregate view across all open positions: total invested, current
    value at live market price, and unrealized P&L. This build has no live
    exchange-balance service wired in yet (see api/testnet_routes.py
    account()), so "balance" here means capital currently committed to
    open positions, not total wallet balance."""
    repo = PositionRepository(session)
    positions = await repo.open_positions(user.id)
    invested = 0.0
    current_value = 0.0
    rows = []
    for p in positions:
        try:
            data = await ticker(p.symbol)
            current = float(data["lastPrice"])
        except Exception:
            current = p.entry_price
        pos_invested = p.quantity * p.entry_price
        pos_value = p.quantity * current
        invested += pos_invested
        current_value += pos_value
        rows.append({
            "symbol": p.symbol, "quantity": p.quantity,
            "entry_price": p.entry_price, "current_price": current,
            "invested_usdt": round(pos_invested, 2), "value_usdt": round(pos_value, 2),
            "pnl_usdt": round(pos_value - pos_invested, 2),
            "pnl_pct": round((pos_value - pos_invested) / pos_invested * 100, 2) if pos_invested else 0,
        })
    pnl = current_value - invested
    return {
        "open_position_count": len(positions),
        "invested_usdt": round(invested, 2),
        "current_value_usdt": round(current_value, 2),
        "unrealized_pnl_usdt": round(pnl, 2),
        "unrealized_pnl_pct": round(pnl / invested * 100, 2) if invested else 0,
        "positions": rows,
    }


@router.get("/watchlist")
async def watchlist(symbols: str | None = None):
    """Multiple coins at once — price, 24h change, and news sentiment for
    each, in a single call. Public/read-only, same as GET /api/market.
    Pass ?symbols=BTCUSDT,ETHUSDT to override the default list
    (core.config.settings.watchlist_symbols)."""
    syms = [s.strip().upper() for s in symbols.split(",")] if symbols else list(settings.watchlist_symbols)
    if not syms:
        raise HTTPException(400, "No symbols to watch.")

    async def get_ticker(sym):
        try:
            return sym, await ticker(sym)
        except Exception as e:
            return sym, {"error": str(e)}

    ticker_results, news_buckets = await asyncio.gather(
        asyncio.gather(*(get_ticker(s) for s in syms)),
        _news.collect_bulk(syms),
    )
    tickers = dict(ticker_results)

    out = []
    for s in syms:
        t = tickers.get(s, {})
        items = news_buckets.get(s, [])
        summary = await _news.summarize(s, items)
        out.append({
            "symbol": s,
            "price": float(t["lastPrice"]) if "lastPrice" in t else None,
            "change_24h_pct": float(t["priceChangePercent"]) if "priceChangePercent" in t else None,
            "volume_24h": float(t["volume"]) if "volume" in t else None,
            "error": t.get("error"),
            "sentiment": summary["sentiment"],
            "sentiment_score": summary["sentiment_score"],
            "news_count": summary["count"],
        })
    return {"count": len(out), "watchlist": out}


@router.get("/klines/{symbol}")
async def chart_klines(symbol: str, interval: str = "15m", limit: int = 100):
    """Candlestick data for the live price chart. Thin wrapper around
    market.binance_public.klines — public Binance market data, no key
    needed. Returns [open_time, open, high, low, close, volume]."""
    if limit > 500:
        limit = 500
    try:
        raw = await klines(symbol, interval, limit)
    except Exception as e:
        raise HTTPException(502, f"Chart data unavailable: {e}")
    candles = [
        {
            "time": row[0],
            "open": float(row[1]), "high": float(row[2]),
            "low": float(row[3]), "close": float(row[4]),
            "volume": float(row[5]),
        }
        for row in raw
    ]
    return {"symbol": symbol.upper(), "interval": interval, "candles": candles}
