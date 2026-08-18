from __future__ import annotations
from dataclasses import dataclass, asdict


@dataclass
class AgentVote:
    name: str
    action: str
    confidence: float
    reasons: list[str]
    veto: bool = False


class TradingCouncil:
    """Deterministic multi-agent council. Advisory only; risk remains authoritative."""

    def deliberate(
        self,
        *,
        technical: dict,
        news: dict,
        risk: dict,
        regime: dict,
        ml: dict | None,
        orderflow: dict | None = None,
        macro: dict | None = None,
        historical: dict | None = None,
        sentiment: dict | None = None,
    ) -> dict:
        votes: list[AgentVote] = []
        research_conflict = False

        trend = str(technical.get("trend", "")).upper()
        tech_bias = float(technical.get("score", technical.get("signal_score", 0)) or 0)
        if trend == "BULLISH":
            tech_bias += 1
        elif trend == "BEARISH":
            tech_bias -= 1
        votes.append(AgentVote(
            "technical",
            "BUY" if tech_bias > .5 else "SELL" if tech_bias < -.5 else "WAIT",
            min(99, 55 + abs(tech_bias) * 10),
            [f"technical structure; trend={trend or 'UNKNOWN'}"],
        ))

        impact = str(news.get("impact", "UNKNOWN")).upper()
        nscore = float(news.get("sentiment_score", news.get("score", 0)) or 0)
        impact_bias = {"POSITIVE": 0.5, "BULLISH": 0.5, "NEGATIVE": -0.5, "BEARISH": -0.5}.get(impact, 0.0)
        if impact_bias:
            nscore = (nscore * 0.5) + (impact_bias * 0.5)

        research = news.get("ai_research") or {}
        research_status = str(research.get("status", "unavailable"))
        grounded = research.get("grounded_sources") or research.get("sources") or []
        research_conf = max(0.0, min(100.0, float(research.get("confidence", 0) or 0)))
        research_reasons = ["news/sentiment context", f"impact={impact}"]
        if research_status == "ok" and grounded:
            research_reasons.append(f"Gemini grounded research; sources={len(grounded)}")
            research_impact = str(research.get("impact", "")).upper()
            research_bias = 1 if research_impact in {"POSITIVE", "BULLISH"} else -1 if research_impact in {"NEGATIVE", "BEARISH"} else 0
            rss_bias = 1 if impact in {"POSITIVE", "BULLISH"} else -1 if impact in {"NEGATIVE", "BEARISH"} else 0
            research_conflict = bool(rss_bias and research_bias and rss_bias != research_bias)
            if research_conflict:
                research_reasons.append("RSS/Gemini directional conflict; council forced to WAIT")
            else:
                nscore = (nscore * 0.45) + (research_bias * (research_conf / 100) * 0.55)
        else:
            research_reasons.append("grounded Gemini research unavailable; RSS only")
        votes.append(AgentVote(
            "news",
            "WAIT" if research_conflict else ("BUY" if nscore > .2 else "SELL" if nscore < -.2 else "WAIT"),
            min(95, 55 + abs(nscore) * 35),
            research_reasons,
        ))

        prob = float((ml or {}).get("probability_up", .5) or .5)
        votes.append(AgentVote(
            "ml",
            "BUY" if prob >= .57 else "SELL" if prob <= .43 else "WAIT",
            round(50 + abs(prob - .5) * 200, 2),
            ["model probability"] if (ml or {}).get("status") == "OK" else ["model unavailable"],
        ))

        rvol = float(regime.get("volatility", 0) or 0)
        regime_name = str(regime.get("regime", regime.get("name", "UNKNOWN")))
        veto = rvol > .12
        regime_upper = regime_name.upper()
        votes.append(AgentVote(
            "regime",
            "WAIT" if veto else ("BUY" if "BULL" in regime_upper else "SELL" if "BEAR" in regime_upper else "WAIT"),
            70 if not veto else 90,
            [f"regime={regime_name}"],
            veto=veto,
        ))

        if orderflow:
            imb = float(orderflow.get("imbalance", 0) or 0)
            votes.append(AgentVote("orderflow", "BUY" if imb > .12 else "SELL" if imb < -.12 else "WAIT", min(95, 55 + abs(imb) * 100), ["order-book imbalance"]))
        if macro:
            ms = float(macro.get("risk_score", 0) or 0)
            surprise = float(macro.get("surprise_score", 0) or 0)
            votes.append(AgentVote("macro", "WAIT" if ms >= .8 else "BUY" if surprise > .2 else "SELL" if surprise < -.2 else "WAIT", 80 if ms >= .8 else 60, ["macro event state"]))
        if historical:
            d = str(historical.get("direction", "NEUTRAL")).upper()
            votes.append(AgentVote("historical", "BUY" if d == "BULLISH" else "SELL" if d == "BEARISH" else "WAIT", float(historical.get("confidence", 50) or 50), ["chronological historical context"]))
        if sentiment:
            sd = str(sentiment.get("direction", "NEUTRAL")).upper()
            votes.append(AgentVote("sentiment", "BUY" if sd == "BULLISH" else "SELL" if sd == "BEARISH" else "WAIT", float(sentiment.get("confidence", 50) or 50), ["market sentiment context"]))

        counts = {a: 0 for a in ("BUY", "SELL", "WAIT")}
        for vote in votes:
            counts[vote.action] += vote.confidence
        action = max(counts, key=counts.get)
        total = sum(counts.values()) or 1
        confidence = 100 * counts[action] / total
        active = [v for v in votes if v.action in {"BUY", "SELL"}]
        contradiction = int(
            research_conflict
            or (any(v.action == "BUY" for v in active) and any(v.action == "SELL" for v in active))
        )
        return {
            "action": action,
            "confidence": round(confidence, 2),
            "votes": [asdict(v) for v in votes],
            "veto": any(v.veto for v in votes),
            "contradiction_score": contradiction,
            "counts": counts,
        }


class IQ200Council(TradingCouncil):
    """Full debate layer with bull/bear cases and adversarial challenge."""

    def deliberate_full(self, payload: dict) -> dict:
        base = self.deliberate(**payload)
        votes = base["votes"]
        buy = sum(v["confidence"] for v in votes if v["action"] == "BUY")
        sell = sum(v["confidence"] for v in votes if v["action"] == "SELL")
        bull = {"agent": "bull", "action": "BUY" if buy >= sell else "WAIT", "arguments": ["aggregate bullish evidence", "trend/liquidity confirmation required"]}
        bear = {"agent": "bear", "action": "SELL" if sell >= buy else "WAIT", "arguments": ["aggregate bearish evidence", "downside/invalidation must survive challenge"]}
        objections = []
        if base.get("veto"):
            objections.append("regime veto is active")
        if base.get("contradiction_score", 0):
            objections.append("BUY/SELL evidence conflicts")
        if not objections:
            objections.append("no hard contradiction detected; still subject to risk")
        judge_action = "WAIT" if base.get("veto") or base.get("contradiction_score", 0) else base["action"]
        return {
            **base,
            "bull_case": bull,
            "bear_case": bear,
            "adversarial_challenge": {"status": "CHALLENGE", "objections": objections},
            "chief_judge": {"action": judge_action, "confidence": base["confidence"], "reason": "risk/regime veto and contradiction checks applied"},
        }
