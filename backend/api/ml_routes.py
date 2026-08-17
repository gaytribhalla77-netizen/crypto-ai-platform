from fastapi import APIRouter, Depends, HTTPException

from auth.dependencies import get_db_session
from database.repository import PredictionRepository
from ai.ml.predictor import MLPredictor, resolve_due_predictions

router = APIRouter(prefix="/api/ml", tags=["ml"])
_predictor = MLPredictor()


@router.post("/predict/{symbol}")
async def predict(symbol: str, session=Depends(get_db_session)):
    """Runs the trained model (if one exists) and records the prediction
    so it can be scored later against what actually happened. Public,
    read-only in the sense that it never places an order — it only makes
    and logs a forecast."""
    # Resolve anything that's come due first, so accuracy stays current.
    await resolve_due_predictions(session)

    result = await _predictor.predict(symbol)
    if result["status"] != "OK":
        return result

    repo = PredictionRepository(session)
    saved = await repo.create(
        symbol=result["symbol"], interval=result["interval"],
        horizon_candles=result["horizon_candles"], direction=result["direction"],
        confidence=result["confidence"], probability_up=result["probability_up"],
        entry_price=result["entry_price"], model_version=_predictor.model_version(symbol),
        target_time=result["target_time"], resolved=False,
    )
    result["prediction_id"] = saved.id
    return result


@router.get("/accuracy/{symbol}")
async def accuracy(symbol: str, limit: int = 200, session=Depends(get_db_session)):
    """The model's actual, honest track record: of its last N resolved
    predictions for this symbol, how many were right. This is the number
    that answers 'does it know if its own decision was right or wrong' —
    not a number the model reports about itself, but one computed
    independently from stored outcomes."""
    await resolve_due_predictions(session)
    repo = PredictionRepository(session)
    stats = await repo.accuracy_stats(symbol=symbol, limit=limit)
    recent = await repo.recent(symbol=symbol, limit=10)
    stats["symbol"] = symbol.upper()
    stats["recent"] = [
        {
            "id": p.id, "direction": p.direction, "confidence": p.confidence,
            "entry_price": p.entry_price, "exit_price": p.exit_price,
            "resolved": p.resolved, "correct": p.correct,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in recent
    ]
    return stats
