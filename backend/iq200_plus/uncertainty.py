import math
from dataclasses import dataclass

@dataclass(frozen=True)
class Uncertainty:
    mean: float
    std: float
    lower: float
    upper: float
    confidence: float

def estimate(values: list[float], z: float = 1.96) -> Uncertainty:
    if not values:
        return Uncertainty(0.0, float("inf"), float("-inf"), float("inf"), 0.0)
    m = sum(values) / len(values)
    if len(values) == 1:
        return Uncertainty(m, 0.0, m, m, 0.5)
    var = sum((x-m)**2 for x in values) / (len(values)-1)
    sd = math.sqrt(max(var, 0.0))
    se = sd / math.sqrt(len(values))
    lo, hi = m-z*se, m+z*se
    confidence = max(0.0, min(1.0, 1.0 - (hi-lo)/(abs(m)+1e-9)))
    return Uncertainty(m, sd, lo, hi, confidence)
