from dataclasses import dataclass
from collections import defaultdict

@dataclass(frozen=True)
class Pattern:
    conditions: tuple[str, ...]
    count: int
    win_rate: float
    avg_return: float
    lift: float

def discover(records: list[dict], features: list[str], min_count: int = 20) -> list[Pattern]:
    if not records or not features: return []
    base = [float(r.get("return", 0.0)) > 0 for r in records]
    base_rate = sum(base)/len(base)
    groups = defaultdict(list)
    for r in records:
        active = tuple(sorted(f for f in features if bool(r.get(f))))
        if active: groups[active].append(float(r.get("return", 0.0)))
    found=[]
    for cond, vals in groups.items():
        if len(vals) < min_count: continue
        wr=sum(v>0 for v in vals)/len(vals)
        found.append(Pattern(cond,len(vals),wr,sum(vals)/len(vals),wr/(base_rate or 1e-9)))
    return sorted(found,key=lambda p:(p.lift,p.count),reverse=True)
