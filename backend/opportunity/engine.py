from dataclasses import dataclass

@dataclass
class Opportunity:
    symbol: str
    score: float
    reason: str
    suggested_amount_usdt: float

class OpportunityEngine:
    def __init__(self, max_auto_amount_usdt=10.0):
        self.max_auto_amount_usdt = max_auto_amount_usdt

    def rank(self, symbol, confidence, risk, momentum):
        score = max(0.0, min(100.0, confidence*0.7 + momentum*0.3 - risk*0.2))
        return Opportunity(symbol, round(score,2), "Composite opportunity score", min(5.0, self.max_auto_amount_usdt))
