from fastapi import APIRouter, HTTPException, Depends
from ai.orchestrator.service import analyze
from auth.dependencies import get_current_user

router = APIRouter(prefix="/api")

@router.get("/market/{symbol}")
async def market_analysis(symbol: str):
    # Read-only public market data — no auth required.
    try:
        return await analyze(symbol)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Market data unavailable: {e}")

@router.post("/trade/validate")
async def validate_trade(symbol: str, side: str, amount_usdt: float, user=Depends(get_current_user)):
    # This lightweight signature can't evaluate portfolio risk. Use
    # POST /api/trading/risk-check (RiskEngine) for a real trade decision.
    raise HTTPException(
        status_code=400,
        detail="Use POST /api/trading/risk-check for trade validation — it runs "
               "the full per-trade + portfolio risk check.",
    )
