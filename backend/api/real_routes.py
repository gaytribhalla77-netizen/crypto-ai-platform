from __future__ import annotations
import os
import uuid
from decimal import Decimal, ROUND_DOWN, ROUND_UP
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from auth.dependencies import get_current_user, get_db_session, CurrentUser
from database.models import SecuritySetting
from security.vault import CredentialVault
from core.config import settings
from security.totp import verify
from security.kill_switch import is_killed
from trading.risk_manager.engine import risk_engine
from database.repository import TradeRepository, AuditRepository, PositionRepository, DuplicateTradeRequest
from exchanges.binance.client import BinanceClient
from market.fx_adapter import OandaFXAdapter
from execution.fx_oanda import OandaExecution

router = APIRouter(prefix="/api/real", tags=["real-trading"])


from exchanges.binance.safety import symbol_filters as _symbol_filters, floor_step as _floor_step, price_tick as _price_tick


async def _binance_client_for_user(session, user_id: int, *, testnet: bool = False) -> BinanceClient:
    try:
        creds = await CredentialVault().get_provider_credentials(session, user_id, "binance")
        return BinanceClient(creds.get("api_key"), creds.get("api_secret"), testnet=testnet)
    except RuntimeError:
        if not settings.single_operator_mode:
            raise
        return BinanceClient(testnet=testnet)


async def _oanda_clients_for_user(session, user_id: int):
    try:
        creds = await CredentialVault().get_provider_credentials(session, user_id, "oanda")
        token, account_id = creds.get("api_token") or creds.get("token"), creds.get("account_id")
        if not token or not account_id:
            raise RuntimeError("OANDA credentials are incomplete.")
        return OandaFXAdapter(token=token, account_id=account_id), OandaExecution(token=token, account_id=account_id)
    except RuntimeError:
        if not settings.single_operator_mode:
            raise
        return OandaFXAdapter(), OandaExecution()



class BinanceOrder(BaseModel):
    symbol: str
    side: str
    quantity: float = Field(gt=0)
    totp_code: str
    client_request_id: str | None = None


class FXOrder(BaseModel):
    symbol: str
    units: int
    stop_loss: float | None = Field(default=None, gt=0)
    take_profit: float | None = Field(default=None, gt=0)
    totp_code: str
    client_request_id: str | None = None


async def _require_live(user: CurrentUser, session, code: str):
    if os.getenv("LIVE_TRADING", "false").lower() != "true":
        raise HTTPException(409, "Live trading is disabled. Set LIVE_TRADING=true only after broker and risk certification.")
    if os.getenv("LIVE_TRADING_CONFIRM", "") != "I_UNDERSTAND_LIVE_TRADING":
        raise HTTPException(409, "Live trading confirmation is not configured.")
    if await is_killed(session, user.id):
        raise HTTPException(423, "Trading kill switch is enabled.")
    row = (await session.execute(select(SecuritySetting).where(SecuritySetting.user_id == user.id))).scalar_one_or_none()
    if not row or not row.totp_enabled or not row.totp_secret_encrypted:
        raise HTTPException(403, "Live trading requires enabled TOTP 2FA.")
    secret = CredentialVault().decrypt(row.totp_secret_encrypted)["secret"]
    if not verify(secret, code):
        raise HTTPException(401, "Invalid TOTP code.")


async def _binance_server_risk(client: BinanceClient, session, user_id: int, symbol: str, side: str, quantity: float):
    price = float((await client.get_price(symbol))["price"])
    account = await client.get_account()
    balances = {b["asset"].upper(): float(b.get("free", 0) or 0) for b in account.get("balances", [])}
    base = symbol.upper().replace("USDT", "")
    if side.upper() == "BUY":
        amount_usdt = quantity * price
    else:
        if balances.get(base, 0.0) + 1e-12 < quantity:
            raise HTTPException(409, "Insufficient real exchange balance for SELL.")
        amount_usdt = quantity * price
    usdt_free = balances.get("USDT", 0.0)
    total_equity = 0.0
    for asset, qty in balances.items():
        if qty <= 0: continue
        if asset in {"USDT", "USDC", "BUSD"}: total_equity += qty
        else:
            try: total_equity += qty * float((await client.get_price(asset + "USDT"))["price"])
            except Exception: raise HTTPException(503, f"Unable to value real exchange asset {asset}; refusing trade.")
    # Reuse the authoritative daily-loss snapshot mechanism, but feed it the real account equity.
    from datetime import datetime, timezone
    from database.models import DailyEquitySnapshot
    result = await session.execute(select(DailyEquitySnapshot).where(DailyEquitySnapshot.user_id == user_id, DailyEquitySnapshot.date_key == datetime.now(timezone.utc).date().isoformat()))
    snap = result.scalar_one_or_none()
    if snap is None:
        snap = DailyEquitySnapshot(user_id=user_id, date_key=datetime.now(timezone.utc).date().isoformat(), starting_equity_usdt=total_equity)
        session.add(snap); await session.commit()
    daily_loss = max(0.0, (snap.starting_equity_usdt - total_equity) / snap.starting_equity_usdt * 100) if snap.starting_equity_usdt > 0 else 100.0
    open_positions = len(await PositionRepository(session).open_positions(user_id))
    decision = risk_engine.validate(side=side, amount_usdt=amount_usdt, entry_price=price, balance=usdt_free, exposure=max(0.0, total_equity-usdt_free), daily_loss_pct=daily_loss, open_positions=open_positions)
    if not decision.allowed:
        raise HTTPException(409, f"Risk engine rejected live order: {decision.reason}")
    return price, amount_usdt, decision


async def _emergency_flatten_binance(client, symbol, quantity, audit, user_id, trade_id, session):
    try:
        result = await client.place_market_order(symbol, "SELL", quantity, f"ai_emergency_{trade_id}")
        await audit.record("live_emergency_flattened", {"trade_id": trade_id, "quantity": quantity, "exchange_order_id": result.get("orderId")}, user_id)
        return result
    except Exception as exc:
        from security.kill_switch import set_kill_switch
        await set_kill_switch(session, user_id, True)
        await audit.record("live_emergency_flatten_failed_account_frozen", {"trade_id": trade_id, "error": type(exc).__name__}, user_id)
        raise


@router.get("/status")
async def real_status(user: CurrentUser = Depends(get_current_user), session=Depends(get_db_session)):
    broker = os.getenv("BROKER", "binance").lower()
    async def has_provider(name: str) -> bool:
        try:
            await CredentialVault().get_provider_credentials(session, user.id, name)
            return True
        except RuntimeError:
            return settings.single_operator_mode and (
                (name == "binance" and bool(os.getenv("BINANCE_API_KEY") and os.getenv("BINANCE_API_SECRET"))) or
                (name == "oanda" and bool(os.getenv("OANDA_API_TOKEN") and os.getenv("OANDA_ACCOUNT_ID")))
            )
    return {
        "broker": broker,
        "live_trading": os.getenv("LIVE_TRADING", "false").lower() == "true",
        "live_confirmation_configured": os.getenv("LIVE_TRADING_CONFIRM", "") == "I_UNDERSTAND_LIVE_TRADING",
        "binance_credentials_configured": await has_provider("binance"),
        "oanda_credentials_configured": await has_provider("oanda"),
        "ai_credentials_configured": bool(os.getenv("AI_API_KEY")),
        "simulation_fallback": False,
    }


@router.get("/binance/account")
async def binance_account(user: CurrentUser = Depends(get_current_user), session=Depends(get_db_session)):
    client = await _binance_client_for_user(session, user.id, testnet=False)
    try:
        return await client.get_account()
    except Exception as exc:
        raise HTTPException(502, f"Real Binance account unavailable: {type(exc).__name__}")


@router.get("/binance/quote/{symbol}")
async def binance_quote(symbol: str, user: CurrentUser = Depends(get_current_user), session=Depends(get_db_session)):
    try:
        return await (await _binance_client_for_user(session, user.id, testnet=False)).get_ticker(symbol)
    except Exception as exc:
        raise HTTPException(502, f"Real Binance quote unavailable: {type(exc).__name__}")


@router.post("/binance/order")
async def binance_order(body: BinanceOrder, user: CurrentUser = Depends(get_current_user), session=Depends(get_db_session)):
    await _require_live(user, session, body.totp_code)
    if os.getenv("BROKER", "binance").lower() != "binance":
        raise HTTPException(409, "BROKER is not configured for Binance.")
    side = body.side.upper()
    if side not in {"BUY", "SELL"}:
        raise HTTPException(422, "Only BUY and SELL are supported.")
    cid = body.client_request_id or ("ai_" + uuid.uuid4().hex[:24])
    client = await _binance_client_for_user(session, user.id, testnet=False)
    try:
        info = await client.exchange_info(body.symbol)
        filt = _symbol_filters(info, body.symbol)
        price, amount_usdt, decision = await _binance_server_risk(client, session, user.id, body.symbol, side, body.quantity)
        market_step = filt.get("market_step", filt["step"])
        qty = _floor_step(body.quantity, market_step)
        if qty <= 0 or qty < filt.get("market_min_qty", filt["min_qty"]):
            raise HTTPException(409, "Quantity is below Binance market minimum after precision normalization.")
        if qty > filt.get("market_max_qty", filt["max_qty"]):
            raise HTTPException(409, "Quantity exceeds Binance market maximum.")
        if qty * price < filt["min_notional"]:
            raise HTTPException(409, "Order notional is below Binance minimum.")
        positions = PositionRepository(session)
        existing = await positions.open_position_for_symbol(user.id, body.symbol)
        if side == "SELL" and (existing is None or qty > existing.quantity + 1e-12):
            raise HTTPException(409, "SELL must reduce an existing tracked spot position; short selling is disabled.")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(503, f"Live Binance pre-trade validation failed: {type(exc).__name__}")

    trades = TradeRepository(session)
    audit = AuditRepository(session)
    try:
        trade = await trades.create_idempotent(user_id=user.id, symbol=body.symbol.upper(), side=side, amount_usdt=amount_usdt, status="PENDING", client_request_id=cid)
    except DuplicateTradeRequest as exc:
        return {"duplicate": True, "trade_id": exc.existing_trade.id, "status": exc.existing_trade.status}
    await trades.update_status(trade.id, "SUBMITTED")
    try:
        result = await client.place_market_order(body.symbol, side, qty, cid)
    except Exception as exc:
        await trades.update_status(trade.id, "UNKNOWN")
        await audit.record("live_trade_unknown_outcome", {"trade_id": trade.id, "broker": "binance", "error": type(exc).__name__}, user.id)
        raise HTTPException(502, "Live order outcome is unknown; reconciliation is required before retry.")

    status = str(result.get("status", "UNKNOWN")).upper()
    order_id = result.get("orderId")
    await trades.update_status(trade.id, status, order_id=order_id)
    executed_qty = float(result.get("executedQty", 0) or 0)
    quote_qty = float(result.get("cummulativeQuoteQty", 0) or 0)
    fill_price = quote_qty / executed_qty if executed_qty > 0 and quote_qty > 0 else price

    if status == "PARTIALLY_FILLED":
        # A market order should normally complete. Cancel any residual and
        # protect only the amount actually acquired before returning control.
        try: await client.cancel_order(body.symbol, order_id)
        except Exception: pass
    if status not in {"FILLED", "PARTIALLY_FILLED"} or executed_qty <= 0:
        await audit.record("live_trade_not_filled", {"trade_id": trade.id, "status": status}, user.id)
        return {"real": True, "broker": "binance", "trade_id": trade.id, "status": status, "exchange": result}

    if side == "BUY":
        sl = _price_tick(fill_price * (1 - settings.stop_loss_percent / 100), filt["tick"], up=False)
        tp = _price_tick(fill_price * (1 + settings.take_profit_percent / 100), filt["tick"], up=False)
        if not (sl < fill_price < tp) or sl <= 0:
            await audit.record("live_protection_invalid", {"trade_id": trade.id, "fill_price": fill_price, "sl": sl, "tp": tp}, user.id)
            await _emergency_flatten_binance(client, body.symbol, executed_qty, audit, user.id, trade.id, session)
            raise HTTPException(503, "Protection prices invalid; position was flattened or account was frozen.")
        protect_qty = _floor_step(executed_qty, filt["step"])
        if protect_qty <= 0:
            await _emergency_flatten_binance(client, body.symbol, executed_qty, audit, user.id, trade.id, session)
            raise HTTPException(503, "Filled quantity cannot be protected at Binance precision.")
        try:
            oco = await client.order_list_oco(body.symbol, "SELL", protect_qty, tp, sl, list_client_order_id=f"ai_oco_{trade.id}")
        except Exception as exc:
            await audit.record("live_protection_placement_failed", {"trade_id": trade.id, "error": type(exc).__name__}, user.id)
            await _emergency_flatten_binance(client, body.symbol, protect_qty, audit, user.id, trade.id, session)
            raise HTTPException(503, "Exchange-side protection could not be installed; emergency flatten attempted.")
        list_id = str(oco.get("orderListId")) if oco.get("orderListId") is not None else None
        pos = await positions.create(user_id=user.id, symbol=body.symbol.upper(), side="BUY", quantity=protect_qty, entry_price=fill_price, stop_loss_price=sl, take_profit_price=tp, protection_order_list_id=list_id, status="OPEN")
        await audit.record("live_position_opened_protected", {"trade_id": trade.id, "position_id": pos.id, "quantity": protect_qty, "entry_price": fill_price, "stop_loss_price": sl, "take_profit_price": tp, "order_list_id": list_id}, user.id)
        return {"real": True, "broker": "binance", "trade_id": trade.id, "position_id": pos.id, "status": status, "fill_price": fill_price, "stop_loss_price": sl, "take_profit_price": tp, "protection": oco, "exchange": result}

    # Spot SELL is a reduce-only operation in this application. Close the
    # tracked position only after an actual fill. Any remaining quantity is
    # left open and will be reconciled rather than silently marked closed.
    if existing is not None:
        if executed_qty + 1e-12 >= existing.quantity:
            if existing.protection_order_list_id:
                try: await client.cancel_order_list(body.symbol, order_list_id=existing.protection_order_list_id)
                except Exception: pass
            await positions.close(existing.id)
        else:
            existing.quantity = max(0.0, existing.quantity - executed_qty)
            await session.commit()
    await audit.record("live_position_reduced", {"trade_id": trade.id, "executed_qty": executed_qty, "fill_price": fill_price}, user.id)
    return {"real": True, "broker": "binance", "trade_id": trade.id, "status": status, "fill_price": fill_price, "executed_qty": executed_qty, "exchange": result}


@router.get("/fx/quote/{symbol}")
async def fx_quote(symbol: str, user: CurrentUser = Depends(get_current_user), session=Depends(get_db_session)):
    adapter, _ = await _oanda_clients_for_user(session, user.id)
    try:
        return await adapter.quote(symbol)
    except Exception as exc:
        raise HTTPException(502, f"Real OANDA quote unavailable: {type(exc).__name__}")


@router.get("/fx/candles/{symbol}")
async def fx_candles(symbol: str, interval: str = "1h", limit: int = 500, user: CurrentUser = Depends(get_current_user), session=Depends(get_db_session)):
    try:
        adapter, _ = await _oanda_clients_for_user(session, user.id)
        return await adapter.candles(symbol, interval, min(limit, 5000))
    except Exception as exc:
        raise HTTPException(502, f"Real OANDA candles unavailable: {type(exc).__name__}")


@router.get("/fx/account")
async def fx_account(user: CurrentUser = Depends(get_current_user), session=Depends(get_db_session)):
    try:
        _, execution = await _oanda_clients_for_user(session, user.id)
        return await execution.account_summary()
    except Exception as exc:
        raise HTTPException(502, f"Real OANDA account unavailable: {type(exc).__name__}")


@router.post("/fx/order")
async def fx_order(body: FXOrder, user: CurrentUser = Depends(get_current_user), session=Depends(get_db_session)):
    await _require_live(user, session, body.totp_code)
    if os.getenv("BROKER", "binance").lower() != "oanda":
        raise HTTPException(409, "BROKER is not configured for OANDA.")
    cid = body.client_request_id or ("ai_" + uuid.uuid4().hex[:24])
    _, execution = await _oanda_clients_for_user(session, user.id)
    try:
        summary = await execution.account_summary()
        account = summary.get("account", {})
        if str(account.get("currency", "")).upper() != "USD":
            raise HTTPException(409, "Live OANDA risk gate currently requires a USD-denominated account.")
        adapter, _ = await _oanda_clients_for_user(session, user.id)
        quote = await adapter.quote(body.symbol)
        if not body.symbol.upper().replace("/", "_").endswith("_USD"):
            raise HTTPException(409, "Live OANDA risk gate currently requires USD-quoted FX instruments.")
        amount_usd = abs(body.units) * float(quote["mid"])
        balance = float(account.get("marginAvailable", account.get("NAV", 0)) or 0)
        equity = float(account.get("NAV", account.get("balance", 0)) or 0)
        open_positions = len((await execution.open_positions()).get("positions", []))
        daily_loss = max(0.0, (float(account.get("balance", equity)) - equity) / max(float(account.get("balance", equity)), 1e-9) * 100)
        side = "BUY" if body.units > 0 else "SELL"
        decision = risk_engine.validate(side=side, amount_usdt=amount_usd, entry_price=float(quote["mid"]), balance=balance, exposure=max(0.0, equity-balance), daily_loss_pct=daily_loss, open_positions=open_positions)
        if not decision.allowed:
            raise HTTPException(409, f"Risk engine rejected live OANDA order: {decision.reason}")
        trades = TradeRepository(session); audit = AuditRepository(session)
        try:
            trade = await trades.create_idempotent(user_id=user.id, symbol=body.symbol.upper(), side=side, amount_usdt=amount_usd, status="PENDING", client_request_id=cid)
        except DuplicateTradeRequest as exc:
            return {"duplicate": True, "trade_id": exc.existing_trade.id, "status": exc.existing_trade.status}
        await trades.update_status(trade.id, "SUBMITTED")
        try:
            result = await execution.place_market_order(body.symbol, body.units, body.stop_loss, body.take_profit, cid)
        except Exception as exc:
            await trades.update_status(trade.id, "UNKNOWN")
            await audit.record("live_trade_unknown_outcome", {"trade_id": trade.id, "broker": "oanda", "error": type(exc).__name__}, user.id)
            raise HTTPException(502, "Live OANDA order outcome is unknown; reconciliation is required before retry.")
        txn = result.get("orderFillTransaction") or result.get("orderCreateTransaction") or {}
        await trades.update_status(trade.id, "FILLED" if result.get("orderFillTransaction") else "SUBMITTED", order_id=txn.get("id"))
        await audit.record("live_trade_submitted", {"trade_id": trade.id, "broker": "oanda", "status": "FILLED" if result.get("orderFillTransaction") else "SUBMITTED"}, user.id)
        return {"real": True, "broker": "oanda", "trade_id": trade.id, "risk": decision.__dict__, "client_order_id": cid, "exchange": result}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(502, f"Real OANDA order failed: {type(exc).__name__}")
