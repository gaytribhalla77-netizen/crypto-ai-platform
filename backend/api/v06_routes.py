from fastapi import APIRouter, HTTPException, Depends
from ai.brain import ChiefOperator
from ai.orchestrator.service import analyze as advanced_analyze
from news.engine import NewsEngine
from trading.testnet_service import TestnetTradeService
from portfolio.state import PortfolioStateService
from auth.dependencies import get_current_user, get_db_session

router = APIRouter(prefix="/api/v06", tags=["v0.6"])
brain = ChiefOperator()
news = NewsEngine()
testnet = TestnetTradeService()


@router.get("/analyze/{symbol}")
async def analyze(symbol: str):
    return await advanced_analyze(symbol)


@router.post("/testnet/order")
async def testnet_order(
    symbol: str, side: str, amount_usdt: float, price: float, quantity: float,
    client_request_id: str | None = None,
    stop_loss_pct: float | None = None,
    take_profit_pct: float | None = None,
    user=Depends(get_current_user),
    session=Depends(get_db_session),
):
    """Canonical risk-gated testnet order path.

    Portfolio truth is server-owned: the caller cannot submit balance,
    exposure, daily-loss or open-position values. Those are derived from the
    configured exchange account plus the database before risk approval.
    """
    try:
        state = await PortfolioStateService().snapshot_and_risk_state(session, user.id)
        return await testnet.execute(
            session=session, user_id=user.id, symbol=symbol, side=side,
            amount_usdt=amount_usdt, price=price, quantity=quantity,
            balance=state["balance"], exposure=state["exposure"],
            daily_loss_pct=state["daily_loss_pct"], open_positions=state["open_positions"],
            client_request_id=client_request_id,
            stop_loss_pct=stop_loss_pct, take_profit_pct=take_profit_pct,
        )
    except Exception as e:
        raise HTTPException(400, str(e))
