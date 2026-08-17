from fastapi import APIRouter, Depends, HTTPException

from auth.dependencies import get_db_session
from ai.technical.service import technical_analysis
from news.engine import NewsEngine
from intelligence.council_service import build_council
from ai.ml.predictor import MLPredictor, resolve_due_predictions
from database.repository import PredictionRepository

router = APIRouter(prefix="/api/intel", tags=["intel"])
_news = NewsEngine()
_predictor = MLPredictor()


@router.get("/{symbol}")
async def full_intel(symbol: str, session=Depends(get_db_session)):
    try:
        evidence = await build_council(symbol)
    except Exception as exc:
        raise HTTPException(503, f"Intelligence evidence unavailable: {type(exc).__name__}")
    await resolve_due_predictions(session)
    accuracy = await PredictionRepository(session).accuracy_stats(symbol=symbol.upper(), limit=200)
    evidence["ai_track_record"] = accuracy
    return evidence
