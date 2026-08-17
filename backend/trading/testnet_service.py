import uuid
from decimal import Decimal, ROUND_DOWN, ROUND_UP
from database.repository import TradeRepository, AuditRepository, PositionRepository, DuplicateTradeRequest
from exchanges.binance.testnet_client import BinanceTestnetClient
from exchanges.binance.filters import validate_order_filters
from trading.risk_manager.engine import risk_engine
from trading.idempotency import request_key
from security.kill_switch import is_killed
from security.vault import CredentialVault
from core.config import settings


def _parse_lot_and_notional(exchange_info: dict, symbol: str):
    for s in exchange_info.get("symbols", []):
        if s.get("symbol", "").upper() != symbol.upper():
            continue
        min_qty = max_qty = step_size = min_notional = tick_size = None
        for f in s.get("filters", []):
            ftype = f.get("filterType")
            if ftype == "LOT_SIZE":
                min_qty = float(f["minQty"])
                max_qty = float(f["maxQty"])
                step_size = float(f["stepSize"])
            elif ftype in ("MIN_NOTIONAL", "NOTIONAL"):
                min_notional = float(f.get("minNotional", f.get("notional", 0)))
            elif ftype == "PRICE_FILTER":
                tick_size = float(f.get("tickSize", 0))
        if None in (min_qty, max_qty, step_size, min_notional, tick_size):
            raise RuntimeError(f"Could not read LOT_SIZE/MIN_NOTIONAL filters for {symbol}.")
        return min_qty, max_qty, step_size, min_notional, tick_size
    raise RuntimeError(f"Symbol {symbol} not found in exchange info.")


class TestnetTradeService:
    """The risk-gated, idempotent, filter-validated, persisted path to
    Binance testnet. This is what routes should call to place an order —
    not BinanceTestnetClient directly."""

    def __init__(self):
        self.exchange = BinanceTestnetClient()
        self.risk = risk_engine

    async def execute(
        self, *, session, user_id: int, symbol: str, side: str,
        amount_usdt: float, price: float, quantity: float,
        balance: float, exposure: float, daily_loss_pct: float,
        open_positions: int, client_request_id: str | None = None,
        automatic: bool = False,
        stop_loss_pct: float | None = None,
        take_profit_pct: float | None = None,
    ):
        if await is_killed(session, user_id):
            raise RuntimeError("Trading kill switch is enabled for this account.")

        try:
            creds = await CredentialVault().get_provider_credentials(session, user_id, "binance")
            self.exchange = BinanceTestnetClient(creds.get("api_key"), creds.get("api_secret"))
        except RuntimeError:
            if not settings.single_operator_mode:
                raise
            self.exchange = BinanceTestnetClient()

        trades = TradeRepository(session)
        positions = PositionRepository(session)
        audit = AuditRepository(session)

        if not client_request_id:
            # Deterministic fallback so an accidental double-submit of the
            # exact same order (no explicit client ID) still collides,
            # rather than silently creating two trades. A client that wants
            # to legitimately repeat the same params should pass its own
            # unique client_request_id.
            client_request_id = request_key(user_id, symbol, side, amount_usdt, "auto")

        decision = self.risk.validate(
            side=side, amount_usdt=amount_usdt, entry_price=price,
            balance=balance, exposure=exposure, daily_loss_pct=daily_loss_pct,
            open_positions=open_positions, automatic=automatic,
            stop_loss_pct=stop_loss_pct, take_profit_pct=take_profit_pct,
        )
        if not decision.allowed:
            await audit.record("trade_risk_rejected", {"symbol": symbol, "reason": decision.reason}, user_id)
            raise RuntimeError(decision.reason)

        try:
            info = await self.exchange.exchange_info(symbol)
            min_qty, max_qty, step_size, min_notional, tick_size = _parse_lot_and_notional(info, symbol)
        except Exception as e:
            await audit.record("trade_filter_lookup_failed", {"symbol": symbol, "error": str(e)}, user_id)
            raise RuntimeError(f"Could not validate exchange filters, refusing to trade: {e}")

        ok, reason = validate_order_filters(quantity, price, min_qty, max_qty, step_size, min_notional)
        if not ok:
            await audit.record("trade_filter_rejected", {"symbol": symbol, "reason": reason}, user_id)
            raise RuntimeError(f"Exchange filter check failed: {reason}")

        try:
            trade = await trades.create_idempotent(
                user_id=user_id, symbol=symbol.upper(), side=side.upper(),
                amount_usdt=amount_usdt, status="PENDING",
                client_request_id=client_request_id,
            )
        except DuplicateTradeRequest as e:
            await audit.record(
                "trade_duplicate_blocked",
                {"symbol": symbol, "client_request_id": client_request_id, "existing_trade_id": e.existing_trade.id},
                user_id,
            )
            # Do not resubmit to the exchange. Return the existing trade's
            # state so the caller can reconcile instead of double-ordering.
            return {"duplicate": True, "trade_id": e.existing_trade.id, "status": e.existing_trade.status}

        await trades.update_status(trade.id, "SUBMITTED")
        client_order_id = "ai_" + uuid.uuid4().hex[:24]
        try:
            result = await self.exchange.order(symbol, side, quantity, client_order_id)
        except Exception as e:
            # Response lost / network failure: state is UNKNOWN, not FAILED —
            # a human or reconciliation job must check with the exchange
            # before ever retrying, since the order may have actually gone through.
            await trades.update_status(trade.id, "UNKNOWN")
            await audit.record("trade_submit_unknown_outcome", {"trade_id": trade.id, "error": str(e)}, user_id)
            raise RuntimeError(f"Order submission outcome unknown, needs reconciliation: {e}")

        order_status = str(result.get("status", "FILLED")).upper()
        await trades.update_status(trade.id, order_status, order_id=result.get("orderId"))
        await audit.record("trade_submitted", {"trade_id": trade.id, "exchange_response": result}, user_id)

        position_id = None
        filled_statuses = {"FILLED", "PARTIALLY_FILLED"}
        if order_status in filled_statuses:
            if side.upper() == "BUY":
                # Prefer the exchange's actual weighted fill price/quantity
                # over the client's requested quote so SL/TP are anchored to
                # what was really executed.
                filled_qty = float(result.get("executedQty", quantity) or quantity)
                quote_qty = float(result.get("cummulativeQuoteQty", 0) or 0)
                actual_entry = quote_qty / filled_qty if quote_qty > 0 and filled_qty > 0 else price
                sl_pct = stop_loss_pct if stop_loss_pct is not None else self.risk.per_trade.stop_loss_pct
                tp_pct = take_profit_pct if take_profit_pct is not None else self.risk.per_trade.take_profit_pct
                if sl_pct <= 0 or tp_pct <= 0:
                    raise RuntimeError("Invalid protection percentages after fill.")
                if side.upper() == "BUY":
                    actual_sl = actual_entry * (1 - float(sl_pct) / 100)
                    actual_tp = actual_entry * (1 + float(tp_pct) / 100)
                else:
                    actual_sl = actual_entry * (1 + float(sl_pct) / 100)
                    actual_tp = actual_entry * (1 - float(tp_pct) / 100)
                protect_qty = float((Decimal(str(filled_qty)) // Decimal(str(step_size))) * Decimal(str(step_size)))
                if protect_qty <= 0:
                    raise RuntimeError("Filled quantity cannot be protected at exchange precision.")
                actual_sl = float((Decimal(str(actual_sl)) / Decimal(str(tick_size))).to_integral_value(rounding=ROUND_DOWN) * Decimal(str(tick_size)))
                actual_tp = float((Decimal(str(actual_tp)) / Decimal(str(tick_size))).to_integral_value(rounding=ROUND_DOWN) * Decimal(str(tick_size)))
                try:
                    oco = await self.exchange.order_list_oco(symbol, "SELL", protect_qty, actual_tp, actual_sl, f"ai_oco_{trade.id}")
                except Exception as exc:
                    await audit.record("testnet_protection_placement_failed", {"trade_id": trade.id, "error": str(exc)}, user_id)
                    # Flatten the acquired amount before surfacing the failure.
                    try:
                        await self.exchange.order(symbol, "SELL", protect_qty, f"ai_emergency_{trade.id}")
                    except Exception:
                        raise RuntimeError("Testnet protection failed and emergency flatten also failed.")
                    raise RuntimeError("Testnet exchange-side protection could not be installed; position flattened.")
                list_id = str(oco.get("orderListId")) if oco.get("orderListId") is not None else None
                pos = await positions.create(
                    user_id=user_id, symbol=symbol.upper(), side="BUY",
                    quantity=protect_qty, entry_price=actual_entry,
                    stop_loss_price=actual_sl,
                    take_profit_price=actual_tp,
                    protection_order_list_id=list_id,
                    status="OPEN",
                )
                position_id = pos.id
                await audit.record(
                    "position_opened",
                    {"position_id": pos.id, "symbol": symbol.upper(),
                     "stop_loss_price": actual_sl,
                     "take_profit_price": actual_tp,
                     "entry_price": actual_entry, "quantity": filled_qty},
                    user_id,
                )
            else:
                # SELL: best-effort close of the oldest open position for
                # this symbol. This is a simple FIFO close, not partial-size
                # accounting — good enough for the paper/testnet flow this
                # build supports.
                existing = await positions.open_position_for_symbol(user_id, symbol)
                if existing is not None:
                    await positions.close(existing.id)
                    position_id = existing.id
                    await audit.record(
                        "position_closed",
                        {"position_id": existing.id, "symbol": symbol.upper(), "exit_price": price},
                        user_id,
                    )

        return {
            "duplicate": False, "trade_id": trade.id, "status": order_status,
            "exchange": result, "position_id": position_id,
            "stop_loss_price": decision.stop_loss_price,
            "take_profit_price": decision.take_profit_price,
        }

    async def close_protective_position(self, *, session, user_id: int, position, exit_price: float, reason: str):
        """Idempotent protective exit for an already-open BUY position.

        This path is only reachable after the position monitor has detected
        its server-stored SL/TP. It never creates a new exposure and uses a
        deterministic client id so repeated worker ticks cannot double-close.
        """
        if position.status != "OPEN":
            return {"already_closed": True, "position_id": position.id}
        try:
            creds = await CredentialVault().get_provider_credentials(session, user_id, "binance")
            self.exchange = BinanceTestnetClient(creds.get("api_key"), creds.get("api_secret"))
        except RuntimeError:
            if not settings.single_operator_mode:
                raise
            self.exchange = BinanceTestnetClient()
        if position.side.upper() != "BUY":
            raise RuntimeError("Protective close currently supports BUY spot positions only.")
        if exit_price <= 0 or position.quantity <= 0:
            raise RuntimeError("Invalid protective-exit price or quantity.")

        trades = TradeRepository(session)
        audit = AuditRepository(session)
        if position.protection_order_list_id:
            try:
                await self.exchange.cancel_order_list(position.symbol, order_list_id=position.protection_order_list_id)
            except Exception:
                pass
        client_request_id = f"protective_exit_position_{position.id}"
        amount_usdt = position.quantity * exit_price
        try:
            trade = await trades.create_idempotent(
                user_id=user_id, symbol=position.symbol.upper(), side="SELL",
                amount_usdt=amount_usdt, status="PENDING",
                client_request_id=client_request_id,
            )
        except DuplicateTradeRequest as e:
            return {"already_submitted": True, "trade_id": e.existing_trade.id, "position_id": position.id, "status": e.existing_trade.status}

        await trades.update_status(trade.id, "SUBMITTED")
        try:
            result = await self.exchange.order(position.symbol, "SELL", position.quantity, "ai_exit_" + str(position.id))
        except Exception as e:
            await trades.update_status(trade.id, "UNKNOWN")
            await audit.record("protective_exit_unknown_outcome", {"position_id": position.id, "trade_id": trade.id, "reason": reason, "error": str(e)}, user_id)
            raise RuntimeError(f"Protective exit outcome unknown; reconciliation required: {e}")

        status = str(result.get("status", "FILLED")).upper()
        await trades.update_status(trade.id, status, order_id=result.get("orderId"))
        if status == "FILLED":
            await PositionRepository(session).close(position.id)
            await audit.record("protective_position_closed", {
                "position_id": position.id, "trade_id": trade.id, "reason": reason,
                "exit_price": exit_price, "exchange_order_id": result.get("orderId"),
            }, user_id)
        else:
            await audit.record("protective_exit_not_filled", {"position_id": position.id, "trade_id": trade.id, "reason": reason, "exchange_status": status}, user_id)
        return {"already_submitted": False, "trade_id": trade.id, "position_id": position.id, "status": status, "exchange": result}
