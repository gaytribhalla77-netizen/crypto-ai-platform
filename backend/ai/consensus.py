def consensus(technical: dict, news: dict, risk: dict, ml: dict | None = None):
    signals = []
    if technical.get("trend") == "Bullish":
        signals.append(1)
    elif technical.get("trend") == "Bearish":
        signals.append(-1)
    else:
        signals.append(0)

    if news.get("impact") == "POSITIVE":
        signals.append(1)
    elif news.get("impact") == "NEGATIVE":
        signals.append(-1)
    else:
        signals.append(0)

    # Optional: the trained ML model's direction, when one exists for this
    # symbol (ai/ml/predictor.py). Kept optional and last so callers that
    # don't have a trained model yet (status != "OK") see unchanged
    # behavior — this never silently substitutes a guess for a real signal.
    if ml and ml.get("status") == "OK":
        signals.append(1 if ml.get("direction") == "UP" else -1)

    score = sum(signals)
    decision = "BUY_BIAS" if score > 0 else "SELL_BIAS" if score < 0 else "NO_TRADE"
    return {"decision": decision, "score": score, "signals": signals}
