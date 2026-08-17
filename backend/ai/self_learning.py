from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
import json, time, statistics
from backtesting.engine import run_backtest
from ai.validation import walk_forward, monte_carlo_trade_sequence

@dataclass
class Hypothesis:
    name: str
    thesis: str
    status: str='PROPOSED'
    evidence: dict|None=None

class SelfLearningLab:
    """Safe learning loop: no live self-modification. Candidate changes must pass gates."""
    def __init__(self, path: str='data/strategy_learning.jsonl'):
        self.path=Path(path); self.path.parent.mkdir(parents=True,exist_ok=True)
    def propose(self, closes:list[float]) -> list[Hypothesis]:
        return [Hypothesis('momentum-regime-filter','Only trade momentum when recent return agrees with trend.'), Hypothesis('mean-reversion-volatility-gate','Only mean-revert when volatility is below its rolling median.')]
    def evaluate(self, closes:list[float], h:Hypothesis) -> Hypothesis:
        if h.name.startswith('momentum'):
            fn=lambda i,c: 'BUY' if i>=5 and c[i]>c[i-5]*1.003 else ('SELL' if i>=5 and c[i]<c[i-5]*.997 else None)
        else:
            fn=lambda i,c: 'BUY' if i>=10 and c[i]<sum(c[i-10:i])/10*.997 else ('SELL' if i>=10 and c[i]>sum(c[i-10:i])/10*1.003 else None)
        bt=run_backtest(closes,signal_fn=fn); wf=walk_forward(closes,folds=min(5,max(2,len(closes)//40)))
        # returns are approximated from the price series for stress validation
        rets=[closes[i]/closes[i-1]-1 for i in range(1,len(closes)) if closes[i-1]]
        mc=monte_carlo_trade_sequence(rets,simulations=500)
        score=float(bt.return_pct)-0.75*float(bt.max_drawdown_pct)
        passed=score>0 and float(bt.max_drawdown_pct)<35 and bool(wf)
        h.status='PAPER_CANDIDATE' if passed else 'REJECTED'; h.evidence={'backtest':bt.__dict__,'walk_forward':wf,'monte_carlo':mc,'gate_score':round(score,4)}
        return h
    def run(self, closes:list[float]) -> dict:
        hs=[self.evaluate(closes,h) for h in self.propose(closes)]
        approved=[asdict(h) for h in hs if h.status=='PAPER_CANDIDATE']
        record={'ts':time.time(),'candidates':[asdict(h) for h in hs],'approved_for_paper':approved}
        with self.path.open('a',encoding='utf-8') as f: f.write(json.dumps(record)+'\n')
        return record
