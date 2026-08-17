import json
from datetime import datetime
from database.models import OrderReconciliation
from database.repository import TradeRepository

async def reconcile_trade(session, trade, exchange):
    # A crash can happen after the exchange accepted an order but before its
    # orderId was persisted. Reconcile by the client order id in that case;
    # never treat the missing local orderId as permission to resubmit.
    if trade.exchange_order_id:
        payload = await exchange.order_status(trade.symbol, trade.exchange_order_id)
    else:
        payload = await exchange.order_status(trade.symbol, client_order_id=trade.client_request_id)
    status = str(payload.get('status','UNKNOWN')).upper()
    qty = float(payload.get('executedQty',0) or 0)
    quote = float(payload.get('cummulativeQuoteQty',0) or 0)
    avg = quote/qty if qty and quote else float(payload.get('price',0) or 0)
    session.add(OrderReconciliation(trade_id=trade.id, exchange_status=status, executed_qty=qty, avg_price=avg, raw_payload=json.dumps(payload, default=str)))
    await TradeRepository(session).update_status(trade.id, status, order_id=trade.exchange_order_id)
    await session.commit()
    return {'status':status,'trade_id':trade.id,'executed_qty':qty,'avg_price':avg,'exchange':payload}
