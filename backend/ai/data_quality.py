from __future__ import annotations
from datetime import datetime, timezone

def assess_market_data(last_price: float | None, candle_count: int, source_ts=None,
                       max_age_seconds: int = 120) -> dict:
    reasons=[]
    safe=True
    if last_price is None or float(last_price) <= 0:
        safe=False; reasons.append("invalid_last_price")
    if candle_count < 30:
        safe=False; reasons.append("insufficient_candles")
    if source_ts is not None:
        if isinstance(source_ts, str):
            source_ts = datetime.fromisoformat(source_ts.replace("Z", "+00:00"))
        if source_ts.tzinfo is None:
            source_ts = source_ts.replace(tzinfo=timezone.utc)
        age=(datetime.now(timezone.utc)-source_ts).total_seconds()
        if age > max_age_seconds:
            safe=False; reasons.append("stale_data")
    return {"safe": safe, "reasons": reasons, "candle_count": candle_count}
