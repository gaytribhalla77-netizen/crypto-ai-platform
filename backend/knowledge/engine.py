from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any
import hashlib, json

@dataclass(frozen=True)
class KnowledgeItem:
    id: str
    topic: str
    principle: str
    conditions: tuple[str, ...]
    failure_conditions: tuple[str, ...]
    evidence_type: str
    source: str
    reviewed_at: str
    status: str = "ACTIVE"

class TradingKnowledgeEngine:
    """Versioned, evidence-first trading knowledge. It never promotes an unvalidated rule."""
    def __init__(self, items: list[KnowledgeItem] | None = None):
        self.items = items or self._seed()

    def _seed(self):
        now=datetime.now(timezone.utc).isoformat()
        seed=[
            ("risk-position-sizing","Risk before reward","Never size a trade before defining invalidation and maximum loss.",
             ("defined_stop","known_equity","known_fee/slippage_budget"),("unknown_stop","insufficient_balance"),
             "risk-principle","CME education / general risk-management principle"),
            ("trend-confirmation","Trend confirmation","A directional setup needs price-structure confirmation; a single indicator is insufficient.",
             ("structure_confirmed","multi-signal_agreement"),("range_bound","conflicting_timeframes"),
             "market-structure","public technical-analysis canon"),
            ("breakout","Breakout validation","Treat a breakout as unconfirmed until close/volume/liquidity context supports continuation.",
             ("close_beyond_level","volume_or_liquidity_confirmation"),("thin_liquidity","immediate_rejection"),
             "strategy-principle","public market-structure literature"),
            ("mean-reversion","Mean reversion","Mean-reversion signals require a range/stationary regime and must be rejected in strong trends.",
             ("range_regime","deviation_from_reference"),("strong_trend","news_shock"),
             "strategy-principle","public quantitative-finance canon"),
            ("news-risk","News risk","Market-moving breaking news can invalidate technical setups; when impact is uncertain, wait.",
             ("fresh_relevant_news_check","impact_assessment"),("unverified_source","conflicting_reports"),
             "risk-principle","public market-risk practice"),
            ("execution","Execution realism","Backtests must include fees, slippage, liquidity and exchange constraints before promotion.",
             ("fees_modelled","slippage_modelled","exchange_filters"),("missing_costs","lookahead_bias"),
             "backtest-principle","public quantitative backtesting practice"),
        ]
        out=[]
        for topic,title,principle,conds,fails,etype,source in seed:
            raw=f"{topic}|{title}|{principle}|{source}"
            kid=hashlib.sha256(raw.encode()).hexdigest()[:16]
            out.append(KnowledgeItem(kid,topic,principle,tuple(conds),tuple(fails),etype,source,now))
        return out

    def search(self, topic: str|None=None, query: str|None=None) -> list[dict]:
        q=(query or "").lower()
        result=[]
        for i in self.items:
            hay=f"{i.topic} {i.principle} {' '.join(i.conditions)} {' '.join(i.failure_conditions)}".lower()
            if (not topic or i.topic==topic) and (not q or q in hay):
                result.append(asdict(i))
        return result

    def evaluate_setup(self, *, market: dict, news: dict, risk: dict, strategy: dict|None=None) -> dict:
        blockers=[]
        if risk.get("status") not in {"OK","PASS"}:
            blockers.append("risk_not_passed")
        impact=(news or {}).get("market_impact",{})
        if impact.get("severity") in {"CRITICAL","HIGH"}:
            blockers.append("market_moving_news")
        if impact.get("status") in {"UNVERIFIED","CONFLICTING"}:
            blockers.append("news_uncertainty")
        if strategy and strategy.get("validation_status") not in {"VALIDATED","PROMOTED"}:
            blockers.append("strategy_not_validated")
        return {"status":"WAIT" if blockers else "ELIGIBLE_FOR_RISK_REVIEW",
                "blockers":blockers,
                "knowledge_items":[i.id for i in self.items if i.status=="ACTIVE"]}

    def quarantine_lesson(self, lesson: dict) -> dict:
        """New lessons never become live rules automatically."""
        payload=json.dumps(lesson,sort_keys=True,separators=(",",":"))
        return {"id":hashlib.sha256(payload.encode()).hexdigest()[:16],
                "status":"QUARANTINED","requires_backtest":True,
                "requires_out_of_sample":True,"requires_testnet":True}
