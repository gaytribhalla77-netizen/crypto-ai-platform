from __future__ import annotations
import math, random, statistics

def _paths(price: float, drift: float, vol: float, steps: int, sims: int, seed: int):
    rng=random.Random(seed); terminal=[]; max_drawdowns=[]
    for _ in range(sims):
        p=price; peak=p; dd=0.0
        for _ in range(steps):
            z=rng.gauss(0,1); p=max(1e-12,p*math.exp(drift-vol*vol/2+vol*z)); peak=max(peak,p); dd=max(dd,(peak-p)/peak)
        terminal.append(p); max_drawdowns.append(dd)
    return terminal,max_drawdowns

def simulate(price: float, expected_return: float, volatility: float, actions=("BUY","SELL","WAIT"), steps=32, simulations=2000, seed=7):
    price=float(price); vol=max(1e-6,abs(float(volatility))); mu=float(expected_return)
    out={}
    for action in actions:
        sign=1 if action=="BUY" else -1 if action=="SELL" else 0
        terminal,dds=_paths(price, sign*mu, vol, steps, simulations, seed+len(action))
        returns=[sign*(x/price-1) for x in terminal]
        out[action]={"expected_return":round(statistics.fmean(returns),6),"p_profit":round(sum(r>0 for r in returns)/len(returns),4),"p_loss":round(sum(r<0 for r in returns)/len(returns),4),"p95_loss":round(sorted(returns)[max(0,int(.05*len(returns))-1)],6),"avg_max_drawdown":round(statistics.fmean(dds),6)}
    best=max(out, key=lambda a: out[a]["expected_return"]-out[a]["avg_max_drawdown"])
    return {"engine":"market_twin_v1","simulations":simulations,"steps":steps,"actions":out,"preferred_action":best}
