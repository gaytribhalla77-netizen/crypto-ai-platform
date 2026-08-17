"""Exchange-aware protective monitor.

Exchange-side OCO is the primary protection for live Binance positions. This
worker is a secondary safety net: it re-reads live prices and can flatten a
tracked position if an exchange-side protection list has disappeared or the
local price crosses the stored protection threshold.
"""
import asyncio
import logging
from database.session import SessionLocal
from database.repository import PositionRepository, AuditRepository, TradeRepository, DuplicateTradeRequest
from database.models import Position
from trading.position_monitor import PositionMonitor
from exchanges.binance.client import BinanceClient
from security.vault import CredentialVault
from security.kill_switch import set_kill_switch
from core.config import settings

logger = logging.getLogger("workers.position_monitor")

class PositionMonitorWorker:
    def __init__(self, interval_seconds: int = 15):
        self.interval_seconds = interval_seconds
        self.monitor = PositionMonitor()

    async def _live_client(self, session, user_id):
        try:
            creds = await CredentialVault().get_provider_credentials(session, user_id, "binance")
            return BinanceClient(creds.get("api_key"), creds.get("api_secret"), testnet=False)
        except RuntimeError:
            if not settings.single_operator_mode:
                raise
            return BinanceClient(testnet=False)

    async def _live_protective_exit(self, session, position: Position, current_price: float, reason: str):
        client = await self._live_client(session, position.user_id)
        audit = AuditRepository(session)
        trades = TradeRepository(session)
        # Cancel the OCO first so a worker-triggered emergency exit cannot race
        # an exchange-side stop/take-profit order.
        if position.protection_order_list_id:
            try:
                await client.cancel_order_list(position.symbol, order_list_id=position.protection_order_list_id)
            except Exception as exc:
                await audit.record("live_protection_cancel_failed", {"position_id": position.id, "error": type(exc).__name__}, position.user_id)
        cid = f"protective_exit_position_{position.id}"
        try:
            trade = await trades.create_idempotent(user_id=position.user_id, symbol=position.symbol, side="SELL", amount_usdt=position.quantity * current_price, status="PENDING", client_request_id=cid)
        except DuplicateTradeRequest as exc:
            return {"duplicate": True, "trade_id": exc.existing_trade.id}
        await trades.update_status(trade.id, "SUBMITTED")
        try:
            result = await client.place_market_order(position.symbol, "SELL", position.quantity, f"ai_exit_{position.id}")
        except Exception as exc:
            await trades.update_status(trade.id, "UNKNOWN")
            await set_kill_switch(session, position.user_id, True)
            await audit.record("live_protective_exit_failed_account_frozen", {"position_id": position.id, "trade_id": trade.id, "error": type(exc).__name__}, position.user_id)
            raise
        status = str(result.get("status", "UNKNOWN")).upper()
        await trades.update_status(trade.id, status, order_id=result.get("orderId"))
        if status == "FILLED":
            await PositionRepository(session).close(position.id)
            await audit.record("live_protective_position_closed", {"position_id": position.id, "trade_id": trade.id, "reason": reason, "exchange_order_id": result.get("orderId")}, position.user_id)
        return {"trade_id": trade.id, "status": status, "exchange": result}

    async def run_once(self):
        async with SessionLocal() as session:
            repo = PositionRepository(session)
            audit = AuditRepository(session)
            positions = await repo.all_open_positions()
            results = []
            for position in positions:
                try:
                    if settings.live_trading:
                        client = await self._live_client(session, position.user_id)
                        current = float((await client.get_price(position.symbol))["price"])
                    else:
                        from market.binance_public import ticker
                        current = float((await ticker(position.symbol))["lastPrice"])
                    result = {"position_id": position.id, "symbol": position.symbol, "current_price": current}
                    # For live Binance, the exchange-side OCO is authoritative.
                    # If it has already completed, reconcile the local position
                    # instead of sending a second market sell.
                    if settings.live_trading and position.protection_order_list_id:
                        try:
                            oco = await client.get_order_list(order_list_id=position.protection_order_list_id)
                            oco_status = str(oco.get("listStatusType", oco.get("listOrderStatus", ""))).upper()
                            child_orders = oco.get("orders") or []
                            filled = any(str(o.get("status", "")).upper() == "FILLED" for o in child_orders)
                            if filled:
                                await repo.close(position.id)
                                await audit.record("live_oco_exit_reconciled", {"position_id": position.id, "order_list_id": position.protection_order_list_id, "oco_status": oco_status}, position.user_id)
                                result.update({"oco_reconciled": True, "oco_status": oco_status})
                                results.append(result)
                                continue
                        except Exception as exc:
                            await audit.record("live_oco_status_unavailable", {"position_id": position.id, "error": type(exc).__name__}, position.user_id)
                            # Do not send a competing market order when we cannot
                            # determine whether the exchange protection already fired.
                            result.update({"oco_status_unavailable": True})
                            results.append(result)
                            continue
                    evaluation = self.monitor.evaluate(position.side, position.entry_price, current, position.stop_loss_price, position.take_profit_price)
                    result["evaluation"] = evaluation
                    if evaluation["action"] == "EXIT":
                        await audit.record("position_exit_condition_detected", {"position_id": position.id, "symbol": position.symbol, "evaluation": evaluation}, position.user_id)
                        try:
                            if settings.live_trading:
                                result["protective_exit"] = await self._live_protective_exit(session, position, current, "stop_loss_or_take_profit")
                            else:
                                from trading.testnet_service import TestnetTradeService
                                result["protective_exit"] = await TestnetTradeService().close_protective_position(session=session, user_id=position.user_id, position=position, exit_price=current, reason="stop_loss_or_take_profit")
                        except Exception as exc:
                            logger.exception("protective exit failed for position %s", position.id)
                            result["protective_exit_error"] = "reconciliation_required"
                    results.append(result)
                except Exception as exc:
                    logger.exception("position monitor failed for position %s", position.id)
                    results.append({"position_id": position.id, "error": type(exc).__name__})
            return results

    async def run_forever(self):
        while True:
            try:
                await self.run_once()
            except Exception:
                logger.exception("position_monitor tick failed")
            await asyncio.sleep(self.interval_seconds)
