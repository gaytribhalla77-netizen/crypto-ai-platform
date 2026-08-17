from __future__ import annotations

def analyze_orderbook(bids: list[list[float]], asks: list[list[float]], depth: int=20) -> dict:
    b=bids[:depth]; a=asks[:depth]
    bid_vol=sum(float(x[1]) for x in b if len(x)>=2); ask_vol=sum(float(x[1]) for x in a if len(x)>=2)
    total=bid_vol+ask_vol
    imbalance=(bid_vol-ask_vol)/total if total else 0.0
    best_bid=float(b[0][0]) if b else 0.0; best_ask=float(a[0][0]) if a else 0.0
    spread=(best_ask-best_bid)/((best_ask+best_bid)/2) if best_bid and best_ask else 0.0
    return {'bid_volume':bid_vol,'ask_volume':ask_vol,'imbalance':round(imbalance,6),'spread_pct':round(spread*100,6),'best_bid':best_bid,'best_ask':best_ask,'liquidity_ok':bool(total and spread >= 0),'depth_used':depth}
