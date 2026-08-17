from __future__ import annotations
from dataclasses import dataclass,asdict
from ai.pattern_discovery import discover_patterns
from ai.self_learning import SelfLearningLab

@dataclass
class ResearchCandidate:
    thesis:str
    evidence:dict
    status:str='PROPOSED'

class AutonomousResearchLab:
    """Discovers hypotheses from supplied observations, then delegates to validated gates."""
    def discover(self, rows:list[dict]):
        patterns=discover_patterns(rows)
        return [ResearchCandidate(
            thesis=' + '.join(p['features'])+' is associated with positive forward returns',
            evidence=p
        ) for p in patterns]
    def validate_price_series(self, closes:list[float]):
        return SelfLearningLab().run(closes)
