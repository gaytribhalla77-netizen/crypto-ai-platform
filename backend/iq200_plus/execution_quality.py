from dataclasses import dataclass

@dataclass(frozen=True)
class ExecutionQuality:
    decision_price: float
    fill_price: float
    side: str
    slippage_bps: float
    latency_ms: float
    filled_qty: float
    requested_qty: float
    fill_ratio: float

def measure(decision_price, fill_price, side, requested_qty, filled_qty, latency_ms):
    if decision_price <= 0: raise ValueError("decision_price must be positive")
    direction = 1 if side.upper()=="BUY" else -1
    bps = ((fill_price-decision_price)/decision_price)*10000*direction
    ratio = filled_qty/requested_qty if requested_qty else 0.0
    return ExecutionQuality(decision_price,fill_price,side.upper(),bps,latency_ms,filled_qty,requested_qty,ratio)
