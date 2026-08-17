"""
Trains a direction-prediction model on real historical price data and
reports its accuracy on data it never saw during training (a time-based
holdout, not a random split — random splits leak future information into
training for time series and would make the reported accuracy fake).

This is a genuinely trained model, not an LLM wrapper: a scikit-learn
classifier fit on technical-indicator features (ai/ml/features.py) computed
from real Binance kline history.

Usage:
    cd backend
    python -m ai.ml.train --symbol BTCUSDT --interval 15m --horizon 4 --candles 3000

--horizon 4 with --interval 15m means "predict whether price will be higher
1 hour from now" (4 candles x 15m). Increase --candles for a larger, more
reliable backtest (Binance allows deep history; more data = slower fetch,
better estimate).
"""
import argparse
import asyncio
import json
import os
from datetime import datetime, timezone

import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, confusion_matrix

from market.binance_public import klines_history
from ai.ml.features import klines_to_df, build_labeled_dataset, FEATURE_COLUMNS

MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")


def _model_path(symbol: str, interval: str, horizon: int) -> str:
    return os.path.join(MODEL_DIR, f"{symbol.upper()}_{interval}_{horizon}.joblib")


async def train(symbol: str, interval: str, horizon: int, candles: int, threshold_pct: float):
    print(f"Fetching ~{candles} historical {interval} candles for {symbol.upper()}...")
    raw = await klines_history(symbol, interval, candles)
    if len(raw) < 200:
        raise RuntimeError(f"Only got {len(raw)} candles — not enough to train on. Try a longer/older interval.")
    df = klines_to_df(raw)
    data = build_labeled_dataset(df, horizon=horizon, threshold_pct=threshold_pct)
    if len(data) < 150:
        raise RuntimeError(f"Only {len(data)} usable rows after feature warm-up/label alignment — need more candles.")

    # Time-based split: train on the older ~80%, test on the newer ~20%.
    # This simulates "train on the past, predict the future" honestly.
    split = int(len(data) * 0.8)
    train_df, test_df = data.iloc[:split], data.iloc[split:]

    X_train, y_train = train_df[FEATURE_COLUMNS].values, train_df["label"].values.astype(int)
    X_test, y_test = test_df[FEATURE_COLUMNS].values, test_df["label"].values.astype(int)

    scaler = StandardScaler().fit(X_train)
    X_train_s, X_test_s = scaler.transform(X_train), scaler.transform(X_test)

    model = LogisticRegression(max_iter=500, class_weight="balanced")
    model.fit(X_train_s, y_train)

    preds = model.predict(X_test_s)
    acc = accuracy_score(y_test, preds)
    prec = precision_score(y_test, preds, zero_division=0)
    rec = recall_score(y_test, preds, zero_division=0)
    cm = confusion_matrix(y_test, preds).tolist()
    baseline = max(y_test.mean(), 1 - y_test.mean())  # accuracy of "always predict the majority class"

    print("\n--- Backtest results (on data the model never trained on) ---")
    print(f"Test samples: {len(y_test)}")
    print(f"Accuracy:  {acc*100:.1f}%")
    print(f"Precision: {prec*100:.1f}%  Recall: {rec*100:.1f}%")
    print(f"Naive baseline (always guess majority class): {baseline*100:.1f}%")
    print(f"Confusion matrix [[TN, FP],[FN, TP]]: {cm}")
    if acc <= baseline + 0.02:
        print("\n⚠️  Accuracy is close to (or below) the naive baseline — this model is not")
        print("    finding a real edge for this symbol/interval/horizon. That's a common,")
        print("    honest result for short-horizon crypto direction. Don't deploy it as-is.")

    os.makedirs(MODEL_DIR, exist_ok=True)
    meta = {
        "symbol": symbol.upper(), "interval": interval, "horizon_candles": horizon,
        "threshold_pct": threshold_pct, "trained_at": datetime.now(timezone.utc).isoformat(),
        "test_accuracy": round(acc, 4), "test_precision": round(prec, 4), "test_recall": round(rec, 4),
        "naive_baseline_accuracy": round(baseline, 4), "test_samples": len(y_test),
        "train_samples": len(y_train), "feature_columns": FEATURE_COLUMNS,
    }
    path = _model_path(symbol, interval, horizon)
    joblib.dump({"model": model, "scaler": scaler, "meta": meta}, path)
    print(f"\nSaved model to {path}")
    print(json.dumps(meta, indent=2))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--symbol", required=True)
    p.add_argument("--interval", default="15m")
    p.add_argument("--horizon", type=int, default=4, help="candles ahead to predict")
    p.add_argument("--candles", type=int, default=3000, help="how much history to fetch")
    p.add_argument("--threshold-pct", type=float, default=0.0,
                    help="min forward % move to count as UP (0 = any positive move)")
    args = p.parse_args()
    asyncio.run(train(args.symbol, args.interval, args.horizon, args.candles, args.threshold_pct))


if __name__ == "__main__":
    main()
