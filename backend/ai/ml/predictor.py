import os
from datetime import datetime, timedelta, timezone

import joblib

from market.binance_public import ticker, klines
from ai.ml.features import klines_to_df, compute_features, FEATURE_COLUMNS
from ai.ml.train import _model_path
from database.repository import PredictionRepository

_INTERVAL_MINUTES = {
    "1m": 1, "3m": 3, "5m": 5, "15m": 15, "30m": 30,
    "1h": 60, "2h": 120, "4h": 240, "1d": 1440,
}


class MLPredictor:
    """Loads a model trained by ai.ml.train and produces a prediction — or,
    if nothing has been trained yet for this symbol/interval/horizon, says
    so plainly (fail-closed, same pattern as provider boundary) instead
    of guessing."""

    def __init__(self, interval: str = "15m", horizon: int = 4):
        self.interval = interval
        self.horizon = horizon

    def _load(self, symbol: str):
        path = _model_path(symbol, self.interval, self.horizon)
        if not os.path.exists(path):
            return None
        return joblib.load(path)

    async def predict(self, symbol: str) -> dict:
        bundle = self._load(symbol)
        if bundle is None:
            return {
                "symbol": symbol.upper(), "status": "NOT_TRAINED",
                "message": (
                    f"No trained model for {symbol.upper()} at {self.interval}/{self.horizon} candles yet. "
                    f"Train one first: python -m ai.ml.train --symbol {symbol.upper()} "
                    f"--interval {self.interval} --horizon {self.horizon}"
                ),
            }
        model, scaler, meta = bundle["model"], bundle["scaler"], bundle["meta"]

        raw = await klines(symbol, self.interval, 60)
        df = klines_to_df(raw)
        feats = compute_features(df)
        latest = feats.iloc[[-1]][FEATURE_COLUMNS]
        if latest.isnull().values.any():
            return {"symbol": symbol.upper(), "status": "INSUFFICIENT_DATA",
                     "message": "Not enough recent candles to compute all indicators yet."}

        X = scaler.transform(latest.values)
        proba_up = float(model.predict_proba(X)[0][1])
        direction = "UP" if proba_up >= 0.5 else "DOWN"
        confidence = round(max(proba_up, 1 - proba_up) * 100, 1)
        entry_price = float(df["close"].iloc[-1])
        minutes = _INTERVAL_MINUTES.get(self.interval, 15) * self.horizon
        target_time = datetime.now(timezone.utc) + timedelta(minutes=minutes)

        return {
            "symbol": symbol.upper(), "status": "OK",
            "direction": direction, "confidence": confidence, "probability_up": round(proba_up, 4),
            "interval": self.interval, "horizon_candles": self.horizon,
            "entry_price": entry_price, "target_time": target_time.isoformat(),
            "model_backtest_accuracy_pct": round(meta.get("test_accuracy", 0) * 100, 1),
            "model_trained_at": meta.get("trained_at"),
            "disclaimer": "Statistical model, not financial advice. Backtest accuracy is not a "
                           "guarantee of future accuracy — see /api/ml/accuracy for the model's "
                           "live, ongoing track record on predictions it actually made.",
        }

    def model_version(self, symbol: str) -> str:
        return f"{symbol.upper()}_{self.interval}_{self.horizon}"


async def resolve_due_predictions(session) -> int:
    """Checks every unresolved prediction whose target_time has passed,
    fetches the real price now, and records whether the model was right.
    Called opportunistically (see api/ml_routes.py) rather than needing a
    separate always-on worker process."""
    repo = PredictionRepository(session)
    due = await repo.due_unresolved(datetime.now(timezone.utc))
    resolved_count = 0
    for pred in due:
        try:
            data = await ticker(pred.symbol)
            exit_price = float(data["lastPrice"])
        except Exception:
            continue
        actual_up = exit_price > pred.entry_price
        correct = actual_up if pred.direction == "UP" else not actual_up
        await repo.resolve(pred.id, exit_price, correct)
        resolved_count += 1
    return resolved_count
