from __future__ import annotations
from dataclasses import dataclass
from statistics import pstdev

@dataclass(frozen=True)
class Regime:
    name: str
    confidence: float
    volatility: float
    trend_strength: float
    reason: str


def detect_regime(closes: list[float], lookback: int = 30) -> Regime:
    values = [float(x) for x in closes if float(x) > 0]
    if len(values) < max(10, lookback):
        return Regime("UNKNOWN", 0.0, 0.0, 0.0, "Insufficient price history")
    w = values[-lookback:]
    returns = [(b-a)/a for a,b in zip(w,w[1:]) if a]
    vol = pstdev(returns) if len(returns) > 1 else 0.0
    fast = sum(w[-7:]) / 7
    slow = sum(w[-21:]) / 21
    slope = (w[-1] / w[0] - 1) if w[0] else 0.0
    trend = min(1.0, abs(slope) / max(vol * 5, 1e-9))
    if vol > 0.02:
        name = "HIGH_VOLATILITY"
    elif trend > 0.75:
        name = "TREND_UP" if fast > slow else "TREND_DOWN"
    elif vol < 0.004:
        name = "LOW_VOLATILITY_RANGE"
    else:
        name = "RANGE"
    confidence = min(1.0, 0.35 + trend * 0.45 + min(vol / 0.02, 1) * 0.20)
    return Regime(name, round(confidence,4), round(vol,6), round(trend,4),
                  f"slope={slope:.4%}, volatility={vol:.4%}, fast_sma_vs_slow={fast/slow-1:.4%}")
