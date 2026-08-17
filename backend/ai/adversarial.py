from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class Challenge:
    approved: bool
    score: float
    objections: list[str]
    required_action: str


def challenge_trade(decision: str, confidence: float, risk: dict, regime: dict,
                     data_quality: dict | None = None) -> Challenge:
    decision = decision.upper()
    objections: list[str] = []
    score = float(confidence) / 100.0
    if decision not in {"BUY", "SELL"}:
        return Challenge(False, 0.0, ["No actionable direction"], "NO_TRADE")
    if risk.get("status") in {"BLOCK", "HIGH", "UNKNOWN"} or risk.get("risk") in {"HIGH", "UNKNOWN"}:
        objections.append("Risk layer is not safely green")
        score -= 0.35
    if regime.get("name") == "UNKNOWN":
        objections.append("Market regime is unknown")
        score -= 0.20
    if data_quality and not data_quality.get("safe", False):
        objections.append("Market data quality is unsafe")
        score -= 0.35
    if confidence < 65:
        objections.append("Decision confidence below challenge threshold")
        score -= 0.15
    score = max(0.0, min(1.0, score))
    approved = score >= 0.60 and not objections[:1]
    return Challenge(approved, round(score,4), objections, "APPROVE" if approved else "REJECT")
