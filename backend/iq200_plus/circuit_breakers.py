from dataclasses import dataclass

@dataclass
class BreakerState:
    stale_data: bool=False
    broker_down: bool=False
    abnormal_spread: bool=False
    max_drawdown: bool=False
    model_drift: bool=False
    reconciliation_unknown: bool=False

class TradingCircuitBreaker:
    def __init__(self): self.state=BreakerState()
    def blocked(self)->bool: return any(vars(self.state).values())
    def reasons(self)->list[str]: return [k for k,v in vars(self.state).items() if v]
    def assert_tradeable(self):
        if self.blocked(): raise RuntimeError("TRADING_BLOCKED:"+",".join(self.reasons()))
