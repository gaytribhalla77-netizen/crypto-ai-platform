from __future__ import annotations
from dataclasses import dataclass, asdict
from itertools import combinations
from statistics import mean

@dataclass(frozen=True)
class Pattern:
    features: tuple[str, ...]
    support: int
    win_rate: float
    avg_return: float
    lift: float


def _bucket(v: float, threshold: float) -> str:
    return 'HIGH' if v > threshold else 'LOW'


def discover_patterns(rows: list[dict], *, min_support: int = 20, min_lift: float = 1.05) -> list[dict]:
    """Mine auditable feature=value conjunctions from supplied labeled data.

    No synthetic labels are generated. A returned pattern is evidence only;
    it is not a live strategy and cannot bypass validation/governance.
    """
    if not rows: return []
    labels=[float(r.get('forward_return',0))>0 for r in rows]
    base=mean(labels)
    if base<=0 or base>=1: return []
    buckets=[]
    for r in rows:
        buckets.append({
            'trend': 'BULL' if float(r.get('trend_strength',0))>0 else 'BEAR',
            'volatility': _bucket(float(r.get('volatility',0)),float(r.get('volatility_median',0))),
            'orderflow': _bucket(float(r.get('orderflow_imbalance',0)),0.05),
            'macro_surprise': _bucket(float(r.get('macro_surprise',0)),0.1),
            'news': _bucket(float(r.get('news_score',0)),0.1),
            'spread': _bucket(float(r.get('spread',0)),float(r.get('spread_median',0))),
        })
    tokens=sorted({f'{k}={v}' for b in buckets for k,v in b.items()})
    out=[]
    for size in (1,2,3):
        for combo in combinations(tokens,size):
            groups=[]
            for i,b in enumerate(buckets):
                if all(b[token.split('=',1)[0]]==token.split('=',1)[1] for token in combo): groups.append(i)
            if len(groups)<min_support: continue
            wr=mean(labels[i] for i in groups); lift=wr/base
            if lift>=min_lift:
                avg=mean(float(rows[i].get('forward_return',0)) for i in groups)
                out.append(asdict(Pattern(combo,len(groups),round(wr,6),round(avg,8),round(lift,6))))
    return sorted(out,key=lambda x:(x['lift'],x['support']),reverse=True)
