from __future__ import annotations
from dataclasses import dataclass, asdict
from statistics import mean
from ai.council import TradingCouncil

@dataclass
class CalibratedVote:
    agent: str
    action: str
    raw_confidence: float
    calibrated_confidence: float
    evidence: list[str]

class IndependentCouncil:
    """Independent evidence channels + calibration + contradiction score.
    It remains advisory; RiskEngine is the final safety authority.
    """
    def __init__(self): self.base=TradingCouncil()
    def deliberate(self, payload: dict):
        result=self.base.deliberate(**payload)
        votes=[]
        for v in result['votes']:
            # Conservative calibration: disagreement lowers confidence.
            cal=max(0,min(100,float(v['confidence'])*(0.65 if result['counts']['WAIT'] else 0.85)))
            votes.append(asdict(CalibratedVote(v['name'],v['action'],float(v['confidence']),round(cal,3),v['reasons'])))
        non_wait=[v for v in votes if v['action']!='WAIT']
        actions={v['action'] for v in non_wait}
        contradiction=1.0 if {'BUY','SELL'}<=actions else 0.0
        return {**result,'votes':votes,'contradiction_score':contradiction,'independent_channels':len(votes),'calibration':'conservative-v1'}
