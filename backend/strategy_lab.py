from __future__ import annotations
from dataclasses import dataclass
from backtesting.engine import run_backtest

@dataclass
class StrategyCandidate:
    name:str; score:float; metrics:dict; status:str

class StrategyLab:
    def evaluate(self, closes:list[float]) -> list[StrategyCandidate]:
        candidates=[]
        for name, fn in [
            ("momentum", lambda i,c: "BUY" if i>=3 and c[i]>c[i-3]*1.002 else ("SELL" if i>=3 and c[i]<c[i-3]*0.998 else None)),
            ("mean_reversion", lambda i,c: "BUY" if i>=5 and c[i]<sum(c[i-5:i])/5*0.995 else ("SELL" if i>=5 and c[i]>sum(c[i-5:i])/5*1.005 else None)),
        ]:
            r=run_backtest(closes,signal_fn=fn)
            score=r.return_pct-(r.max_drawdown_pct*0.5)
            candidates.append(StrategyCandidate(name,round(score,4),r.__dict__,"CANDIDATE"))
        return sorted(candidates,key=lambda x:x.score,reverse=True)
    def promote(self, candidates, min_score:float=0.0):
        if not candidates:return None
        best=candidates[0]
        return {"strategy":best.name,"status":"PROMOTED" if best.score>=min_score else "QUARANTINED","score":best.score}
