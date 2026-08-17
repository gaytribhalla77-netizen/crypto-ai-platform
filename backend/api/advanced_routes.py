from fastapi import APIRouter, Depends, HTTPException
from ai.orchestrator.service import analyze
from strategy_lab import StrategyLab
from ai.regime import detect_regime
from backtesting.engine import run_backtest
from ai.validation import walk_forward, monte_carlo_trade_sequence, model_drift
from auth.dependencies import get_current_user
from core.rate_limit import rate_limit

# Fix: this router previously had zero rate limiting across all 22 routes
# (login was the only rate-limited endpoint in the whole API), including
# compute-heavy ones like Monte Carlo (up to 10k simulations) and
# self-learning. Applying a shared per-IP limiter at the router level
# covers every route here in one place without changing which routes
# require login.
router = APIRouter(
    prefix="/api/advanced",
    tags=["advanced-intelligence"],
    dependencies=[Depends(rate_limit(max_calls=30, window_seconds=60))],
)

@router.get("/analyze/{symbol}")
async def advanced_analysis(symbol: str):
    try:
        return await analyze(symbol)
    except Exception as exc:
        raise HTTPException(503, f"Advanced analysis unavailable: {exc}")

@router.post("/strategy-lab")
async def strategy_lab(closes: list[float]):
    if len(closes) < 40:
        raise HTTPException(400, "At least 40 closes are required.")
    lab=StrategyLab(); candidates=lab.evaluate(closes)
    return {"candidates":[c.__dict__ for c in candidates], "promotion":lab.promote(candidates)}

@router.post("/backtest")
async def backtest(closes: list[float]):
    if len(closes) < 2:
        raise HTTPException(400, "At least 2 closes are required.")
    result=run_backtest(closes)
    return result.__dict__

@router.post("/regime")
async def regime(closes: list[float]):
    if len(closes) < 30:
        raise HTTPException(400, "At least 30 closes are required.")
    return detect_regime(closes).__dict__

@router.post("/walk-forward")
async def walk_forward_api(closes: list[float], folds: int = 4):
    return walk_forward(closes, folds=folds)

@router.post("/monte-carlo")
async def monte_carlo_api(returns: list[float], simulations: int = 1000):
    return monte_carlo_trade_sequence(returns, simulations=simulations)

@router.post("/drift")
async def drift_api(baseline: list[float], recent: list[float]):
    return model_drift(baseline, recent)

from ai.council import TradingCouncil
from ai.market_twin import simulate as market_twin_simulate
from macro.engine import analyze_events
from market.orderflow import analyze_orderbook
from ai.self_learning import SelfLearningLab

@router.post('/council')
async def council(payload: dict):
    return TradingCouncil().deliberate(**payload)

@router.post('/market-twin')
async def market_twin(payload: dict):
    required=('price','expected_return','volatility')
    if any(k not in payload for k in required): raise HTTPException(400, 'price, expected_return and volatility are required')
    return market_twin_simulate(**{k:payload[k] for k in ('price','expected_return','volatility')}, steps=int(payload.get('steps',32)), simulations=min(10000,int(payload.get('simulations',2000))))

@router.post('/macro')
async def macro(payload: dict):
    return analyze_events(payload.get('events', []))

@router.post('/orderflow')
async def orderflow(payload: dict):
    return analyze_orderbook(payload.get('bids', []), payload.get('asks', []), depth=min(100,int(payload.get('depth',20))))

@router.post('/self-learning')
async def self_learning(closes: list[float]):
    if len(closes)<80: raise HTTPException(400,'At least 80 closes are required.')
    return SelfLearningLab().run(closes)

@router.get("/providers/status")
async def provider_status(user=Depends(get_current_user)):
    """Reports real provider configuration only; never reports simulated providers as live.

    Fix: this was previously unauthenticated. It reveals whether broker API
    keys are configured and whether live trading is enabled, which is
    account-relevant information disclosure to anonymous callers — now
    requires a valid logged-in user like every other account-relevant route.
    """
    import os
    return {
        "ai": {"provider": "openai", "configured": bool(os.getenv("AI_API_KEY"))},
        "binance": {"configured": bool(os.getenv("BINANCE_API_KEY") and os.getenv("BINANCE_API_SECRET")), "live_enabled": os.getenv("LIVE_TRADING", "false").lower() == "true" and os.getenv("BROKER", "binance").lower() == "binance"},
        "oanda": {"configured": bool(os.getenv("OANDA_API_TOKEN") and os.getenv("OANDA_ACCOUNT_ID")), "practice": os.getenv("OANDA_PRACTICE", "true").lower() == "true", "live_enabled": os.getenv("LIVE_TRADING", "false").lower() == "true" and os.getenv("BROKER", "binance").lower() == "oanda"},
        "simulation": {"production_fallback": False},
    }

from ai.pattern_discovery import discover_patterns
from ai.research_lab import AutonomousResearchLab
from ai.calibrated_council import IndependentCouncil
from ai.council import IQ200Council
from market.orderflow_advanced import analyze_sequence
from memory.market_memory import MarketMemory, MemoryRecord
from certification.harness import build_certification_plan
from ai.decision_replay import replay_record

@router.post('/research/discover')
async def research_discover(rows: list[dict]):
    if len(rows)<40: raise HTTPException(400,'At least 40 real labeled observations are required.')
    return {'patterns':discover_patterns(rows)}

@router.post('/research/validate')
async def research_validate(closes: list[float]):
    if len(closes)<80: raise HTTPException(400,'At least 80 chronological closes are required.')
    return AutonomousResearchLab().validate_price_series(closes)

@router.post('/council/independent')
async def council_independent(payload: dict):
    return IndependentCouncil().deliberate(payload)

@router.post('/council/full')
async def council_full(payload: dict):
    return IQ200Council().deliberate_full(payload)

@router.post('/orderflow/sequence')
async def orderflow_sequence(payload: dict):
    snaps=payload.get('snapshots',[])
    if len(snaps)<3: raise HTTPException(400,'At least 3 real order-book snapshots are required.')
    return analyze_sequence(snaps,depth=min(100,int(payload.get('depth',20))))

@router.post('/memory/add')
async def memory_add(payload: dict, user=Depends(get_current_user)):
    required=('symbol','regime','action','confidence','features')
    if any(k not in payload for k in required):
        raise HTTPException(400,'symbol, regime, action, confidence and features are required')
    try:
        MarketMemory(user.id).add(MemoryRecord(
            timestamp=payload.get('timestamp', __import__('time').time()),
            **{k: payload[k] for k in required},
            outcome_return=payload.get('outcome_return'),
            outcome_correct=payload.get('outcome_correct'),
            reason=payload.get('reason',''),
        ))
    except ValueError as exc:
        raise HTTPException(413, str(exc))
    return {'stored': True, 'user_id': user.id}

@router.post('/memory/similar')
async def memory_similar(payload: dict, user=Depends(get_current_user)):
    return MarketMemory(user.id).digest(payload.get('features',{}), payload.get('symbol'))

@router.get('/certification/plan')
async def certification_plan():
    return {'real_external_evidence_required':True,'items':[x.__dict__ for x in build_certification_plan()]}

@router.post('/audit/replay')
async def audit_replay(payload: dict):
    return replay_record(payload)
