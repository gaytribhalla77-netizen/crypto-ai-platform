from __future__ import annotations

def brier_score(probabilities:list[float], outcomes:list[int]) -> float:
    if not probabilities or len(probabilities)!=len(outcomes): return 1.0
    return round(sum((float(p)-int(y))**2 for p,y in zip(probabilities,outcomes))/len(outcomes),6)

def calibrate_confidence(confidence:float, brier:float|None) -> float:
    c=max(0.0,min(100.0,float(confidence)))
    if brier is None:return c
    penalty=min(25.0,max(0.0,brier*25.0))
    return round(max(0.0,c-penalty),2)
