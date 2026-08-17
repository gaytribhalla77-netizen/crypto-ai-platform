from __future__ import annotations
from math import sqrt

def correlation(a:list[float], b:list[float]) -> float:
    n=min(len(a),len(b)); a=a[-n:]; b=b[-n:]
    if n<2:return 0.0
    ma=sum(a)/n; mb=sum(b)/n
    num=sum((x-ma)*(y-mb) for x,y in zip(a,b)); da=sum((x-ma)**2 for x in a); db=sum((y-mb)**2 for y in b)
    return num/sqrt(da*db) if da and db else 0.0

def portfolio_metrics(returns: list[float], confidence: float=.95) -> dict:
    if not returns:return {"var_pct":0.0,"cvar_pct":0.0,"volatility_pct":0.0}
    rs=sorted(float(x) for x in returns); idx=max(0,min(len(rs)-1,int((1-confidence)*len(rs))-1)); var=rs[idx]
    tail=[x for x in rs if x<=var]
    cvar=sum(tail)/len(tail) if tail else var
    mean=sum(rs)/len(rs); vol=(sum((x-mean)**2 for x in rs)/len(rs))**0.5
    return {"var_pct":round(var*100,4),"cvar_pct":round(cvar*100,4),"volatility_pct":round(vol*100,4)}
