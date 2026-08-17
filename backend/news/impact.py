from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import re

CRITICAL_TERMS = {
    "hack": 1.0, "exploit": 1.0, "bankruptcy": 1.0, "insolvency": 1.0,
    "war": .9, "invasion": .9, "sanctions": .8, "ban": .8, "lawsuit": .7,
    "etf approval": .9, "etf rejection": -.9, "rate decision": .8,
    "interest rate": .7, "fed": .6, "fomc": .8, "inflation": .6,
    "cpi": .7, "jobs report": .6, "nonfarm payroll": .7,
}
POS = {"approval": .8, "approved": .8, "inflow": .5, "inflows": .5, "adoption": .5,
       "partnership": .35, "surge": .35, "rally": .3, "upgrade": .3, "record": .3}
NEG = {"hack": -1.0, "exploit": -1.0, "outflow": -.5, "outflows": -.5, "crash": -1.0,
       "plunge": -.7, "ban": -.8, "lawsuit": -.5, "liquidation": -.6, "fraud": -1.0,
       "fine": -.5, "delist": -.8, "delisted": -.8}

@dataclass
class ImpactResult:
    score: float
    direction: str
    severity: str
    confidence: float
    affected: bool
    reasons: list[str]

class NewsImpactAnalyzer:
    """Transparent market-impact layer. It distinguishes relevance/severity from sentiment.
    It never claims that a headline guarantees price direction."""
    def analyze(self, items: list[dict], *, now: datetime | None = None) -> dict:
        now = now or datetime.now(timezone.utc)
        if not items:
            return asdict(ImpactResult(0, "UNKNOWN", "UNKNOWN", 0, False, ["No relevant news available"]))
        weighted, reasons, severities = [], [], []
        for item in items:
            title = str(item.get("title", ""))
            t = title.lower()
            age_h = max(0.0, (now - self._parse_dt(item.get("published_at"))).total_seconds() / 3600)
            recency = max(.15, min(1.0, 1.0 - age_h / 72.0))
            s = sum(v for k, v in POS.items() if k in t) + sum(v for k, v in NEG.items() if k in t)
            severity = "LOW"
            for term, mag in CRITICAL_TERMS.items():
                if term in t:
                    severity = "CRITICAL" if abs(mag) >= .9 else "HIGH"
                    reasons.append(f"{severity.lower()} market-moving term: {term}")
                    s += mag
            if abs(s) >= .8: severity = "CRITICAL" if severity == "LOW" else severity
            elif abs(s) >= .45 and severity == "LOW": severity = "MEDIUM"
            weighted.append(s * recency)
            severities.append(severity)
        score = max(-1.0, min(1.0, sum(weighted) / max(1, len(weighted))))
        direction = "BULLISH" if score > .15 else "BEARISH" if score < -.15 else "MIXED"
        severity = "CRITICAL" if "CRITICAL" in severities else "HIGH" if "HIGH" in severities else "MEDIUM" if "MEDIUM" in severities else "LOW"
        confidence = min(95.0, 35.0 + min(len(items), 10) * 5 + (15 if len(set(severities)) > 1 else 0))
        return asdict(ImpactResult(round(score, 3), direction, severity, round(confidence, 2), True, reasons[:20]))

    @staticmethod
    def _parse_dt(value):
        if isinstance(value, datetime): return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        try: return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except Exception: return datetime.now(timezone.utc)
