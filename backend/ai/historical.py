from __future__ import annotations
from statistics import mean

def analyze_historical_context(returns: list[float] | None, *, horizon: int = 20) -> dict:
    """Simple, leakage-resistant historical context summary.
    Caller must provide chronological returns from data available before the decision."""
    rs = [float(x) for x in (returns or []) if isinstance(x, (int, float))]
    if len(rs) < 20:
        return {"status":"INSUFFICIENT_DATA", "sample_size":len(rs), "confidence":0}
    h = max(1, min(horizon, len(rs)))
    recent = rs[-h:]
    avg = mean(recent)
    wins = sum(x > 0 for x in recent)
    return {"status":"OK", "sample_size":len(rs), "horizon":h,
            "mean_return":round(avg,6), "win_rate":round(wins/h,4),
            "direction":"BULLISH" if avg > 0 else "BEARISH" if avg < 0 else "NEUTRAL",
            "confidence":round(min(90, 40 + h*1.5),2),
            "note":"Historical context is evidence, not a profit guarantee."}
