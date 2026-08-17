from fastapi import APIRouter, Depends
from opportunity.engine import OpportunityEngine
from backtesting.engine import run_backtest
from paper_trading.engine import PaperTradingEngine
from trading.risk_manager.engine import risk_engine
from notifications.service import NotificationService
from monitoring.health import health_registry
from auth.dependencies import get_current_user

router = APIRouter(prefix="/api/v09-15", tags=["v0.9-v1.5"])
opps = OpportunityEngine(10)
paper = PaperTradingEngine()
notify = NotificationService()
health = health_registry

@router.get("/opportunity/{symbol}")
async def opportunity(symbol: str, confidence: float=80, risk_score: float=20, momentum: float=80):
    return opps.rank(symbol, confidence, risk_score, momentum).__dict__

@router.post("/paper/order")
async def paper_order(symbol: str, side: str, amount_usdt: float, user=Depends(get_current_user)):
    return paper.order(symbol, side, amount_usdt).__dict__

@router.post("/backtest")
async def backtest(closes: list[float]):
    return run_backtest(closes).__dict__

@router.get("/risk")
async def risk_check():
    # Deprecated: client-supplied portfolio figures were never authoritative.
    # Keep the route but fail safely instead of letting callers mistake it for
    # the canonical risk engine.
    from fastapi import HTTPException
    raise HTTPException(410, "Deprecated. Use POST /api/trading/risk-check with server-observed portfolio state.")

@router.get("/health")
async def health_check():
    return health.snapshot()
