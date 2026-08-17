from dataclasses import dataclass

@dataclass(frozen=True)
class EventImpact:
    surprise: float
    pre_window_return: float
    post_window_return: float
    volatility_change: float
    direction: str

def measure(actual: float, expected: float, pre_return: float, post_return: float, pre_vol: float, post_vol: float)->EventImpact:
    denom=abs(expected) if expected else 1.0
    surprise=(actual-expected)/denom
    direction="UP" if post_return>0 else "DOWN" if post_return<0 else "FLAT"
    return EventImpact(surprise,pre_return,post_return,post_vol-pre_vol,direction)
