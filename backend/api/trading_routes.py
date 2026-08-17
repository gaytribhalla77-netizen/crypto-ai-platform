from fastapi import APIRouter, Depends
from trading.risk_manager.engine import risk_engine, CombinedRiskDecision
from auth.dependencies import get_current_user
from database.session import SessionLocal
from portfolio.state import PortfolioStateService

router = APIRouter(prefix="/api/trading", tags=["trading"])

@router.post("/risk-check")
async def risk_check(
    side: str,
    amount_usdt: float,
    entry_price: float,
    automatic: bool = False,
    stop_loss_pct: float | None = None,
    take_profit_pct: float | None = None,
    user=Depends(get_current_user),
):
    """Authoritative server-side risk check. Client-supplied portfolio
    figures are deliberately not accepted."""
    async with SessionLocal() as session:
        state = await PortfolioStateService().snapshot_and_risk_state(session, user.id)
    decision: CombinedRiskDecision = risk_engine.validate(
        side=side, amount_usdt=amount_usdt, entry_price=entry_price,
        balance=state["balance"], exposure=state["exposure"],
        daily_loss_pct=state["daily_loss_pct"], open_positions=state["open_positions"],
        automatic=automatic, stop_loss_pct=stop_loss_pct,
        take_profit_pct=take_profit_pct,
    )
    result = decision.__dict__.copy()
    result["portfolio"] = state
    return result
