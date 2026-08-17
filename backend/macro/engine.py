from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime, timezone

@dataclass
class MacroEvent:
    name: str
    currency: str
    importance: str = "MEDIUM"
    expected: float | None = None
    actual: float | None = None
    previous: float | None = None
    timestamp: str | None = None

def analyze_events(events: list[dict]) -> dict:
    parsed=[]; surprise_total=0.0; high=0
    for raw in events:
        e=MacroEvent(name=str(raw.get('name','Unknown')), currency=str(raw.get('currency','ALL')).upper(), importance=str(raw.get('importance','MEDIUM')).upper(), expected=raw.get('expected'), actual=raw.get('actual'), previous=raw.get('previous'), timestamp=raw.get('timestamp'))
        surprise=0.0
        if e.expected is not None and e.actual is not None:
            denom=max(abs(float(e.expected)),1e-9); surprise=(float(e.actual)-float(e.expected))/denom
        surprise_total += surprise
        if e.importance == 'HIGH': high += 1
        parsed.append({**asdict(e), 'surprise_score': round(surprise,6)})
    risk=min(1.0, high*.25 + min(.75,abs(surprise_total)*.35))
    return {'events':parsed,'surprise_score':round(surprise_total,6),'high_impact_count':high,'risk_score':round(risk,4),'trade_recommendation':'WAIT' if risk>=.8 else 'NORMAL'}
