from __future__ import annotations

def evaluate_actions(entry: float, expected_return: float, risk_pct: float,
                     volatility: float = 0.0) -> list[dict]:
    """Small deterministic counterfactual layer. It does not predict markets;
    it compares decision choices using the same supplied assumptions."""
    entry = max(float(entry), 1e-9)
    er = float(expected_return)
    rp = max(float(risk_pct), 0.0)
    vol_penalty = min(0.5, float(volatility) * 10)
    actions = [
        ("BUY", er - rp - vol_penalty),
        ("SELL", -er - rp - vol_penalty),
        ("WAIT", -abs(er) * 0.25 - vol_penalty * 0.5),
        ("NO_TRADE", -rp * 0.15),
    ]
    best = max(score for _, score in actions)
    return [{"action": a, "score": round(s,6), "best": s == best} for a,s in actions]
