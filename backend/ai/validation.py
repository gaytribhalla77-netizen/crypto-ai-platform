from __future__ import annotations
import random
from statistics import mean
from backtesting.engine import run_backtest

def walk_forward(closes:list[float], folds:int=4, train_ratio:float=.7)->dict:
    if len(closes)<max(60,folds*20): return {"status":"INSUFFICIENT_DATA","folds":[]}
    size=len(closes)//folds; results=[]
    for i in range(folds):
        start=i*size; end=(i+1)*size if i<folds-1 else len(closes)
        chunk=closes[start:end]
        split=max(2,int(len(chunk)*train_ratio))
        train=chunk[:split]; test=chunk[split:]
        if len(test)<2: continue
        baseline=run_backtest(test)
        results.append({"fold":i+1,"train_size":len(train),"test_size":len(test),"return_pct":baseline.return_pct,"max_drawdown_pct":baseline.max_drawdown_pct,"profit_factor":baseline.profit_factor})
    return {"status":"OK","folds":results,"mean_return_pct":round(mean([x["return_pct"] for x in results]),4) if results else 0.0}

def monte_carlo_trade_sequence(returns:list[float], simulations:int=1000, seed:int=42)->dict:
    if not returns:return {"status":"INSUFFICIENT_DATA"}
    rng=random.Random(seed); finals=[]
    for _ in range(min(simulations,10000)):
        equity=1.0
        for _ in returns: equity*=1+rng.choice(returns)
        finals.append(equity-1)
    finals.sort(); n=len(finals); q=lambda p: finals[min(n-1,max(0,int(n*p)))]
    return {"status":"OK","simulations":n,"p05_return_pct":round(q(.05)*100,4),"median_return_pct":round(q(.50)*100,4),"p95_return_pct":round(q(.95)*100,4)}

def model_drift(baseline:list[float], recent:list[float], threshold:float=.15)->dict:
    if not baseline or not recent:return {"status":"INSUFFICIENT_DATA"}
    bm=mean(baseline); rm=mean(recent); scale=max(abs(bm),.01); drift=abs(rm-bm)/scale
    return {"status":"DRIFT" if drift>=threshold else "STABLE","drift_score":round(drift,4),"threshold":threshold}
