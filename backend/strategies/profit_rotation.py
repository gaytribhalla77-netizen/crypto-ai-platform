"""Side-effect-free small-profit strategy rotation engine.

Default objective: 1.75% NET per completed position. It selects among
explainable price-action families and refuses weak setups. It never submits
orders; execution remains behind the existing authenticated risk gates.
"""
from dataclasses import dataclass, asdict
from math import isfinite
from statistics import mean

@dataclass(frozen=True)
class RotationConfig:
    target_net_pct: float = 1.75
    max_loss_pct: float = 0.90
    fee_rate: float = 0.001
    slippage_rate: float = 0.0005
    min_confidence: float = 0.68
    min_reward_risk: float = 1.5

    @property
    def round_trip_cost_pct(self):
        return 2 * (self.fee_rate + self.slippage_rate) * 100

    @property
    def gross_target_pct(self):
        return self.target_net_pct + self.round_trip_cost_pct

@dataclass(frozen=True)
class StrategyScore:
    name: str
    score: float
    regime_fit: float
    signal_strength: float
    risk_quality: float

@dataclass(frozen=True)
class TradePlan:
    action: str
    strategy: str
    confidence: float
    entry: float | None
    take_profit: float | None
    stop_loss: float | None
    expected_net_pct: float
    reason: str
    candidates: tuple = ()
    def to_dict(self):
        d = asdict(self)
        d['candidates'] = [asdict(x) for x in self.candidates]
        return d

def _ema(values, period):
    if not values: return 0.0
    a = 2 / (period + 1)
    v = float(values[0])
    for p in values[1:]: v = a * float(p) + (1-a) * v
    return v

def _returns(values):
    return [values[i] / values[i-1] - 1 for i in range(1, len(values)) if values[i-1] > 0]

def _rsi(values, period=14):
    rs = _returns(values[-(period+1):])
    gains = [max(x, 0) for x in rs]; losses = [max(-x, 0) for x in rs]
    if not losses or mean(losses) == 0: return 100.0 if gains else 50.0
    return 100 - 100 / (1 + mean(gains) / mean(losses))

def _volatility(values, period=20):
    rs = _returns(values[-(period+1):])
    if len(rs) < 2: return 0.0
    m = mean(rs)
    return mean([(x-m)**2 for x in rs]) ** 0.5 * 100

def _candidate_scores(closes):
    if len(closes) < 30: return ()
    p = closes[-1]; fast = _ema(closes[-20:], 9); slow = _ema(closes[-40:], 21)
    rsi = _rsi(closes); hi = max(closes[-20:-1]); vol = _volatility(closes)
    trend = min(abs(fast-slow) / max(p, 1e-9) * 50, 1)
    stable = 0.35 <= vol <= 3.0
    pullback = fast > slow and 42 <= rsi <= 58
    breakout = p > hi
    reversal = fast < slow and 28 <= rsi <= 40
    candidates = (
        StrategyScore('EMA_TREND_PULLBACK', min(1, .45+trend+(.20 if pullback else 0)), min(1,.55+trend), .78 if pullback else .35, .75 if stable else .45),
        StrategyScore('BREAKOUT_MOMENTUM', min(1,.40+(.35 if breakout else 0)+(.20 if stable else 0)), .80 if breakout else .35, .85 if breakout else .25, .70 if stable else .40),
        StrategyScore('RSI_MEAN_REVERSION', min(1,.40+(.35 if reversal else 0)+(.15 if rsi < 45 else 0)), .65 if reversal else .30, .82 if reversal else .25, .72 if stable else .35),
    )
    return tuple(sorted(candidates, key=lambda x: x.score, reverse=True))

def build_plan(closes, config=None):
    cfg = config or RotationConfig()
    clean = [float(x) for x in closes if isfinite(float(x)) and float(x) > 0]
    if len(clean) < 30:
        return TradePlan('NO_TRADE','NONE',0,None,None,None,0,'Not enough market history.')
    candidates = _candidate_scores(clean); best = candidates[0]; p = clean[-1]
    confidence = min(.99, .55*best.score + .25*best.signal_strength + .20*best.risk_quality)
    target = p * (1 + cfg.gross_target_pct/100); stop = p * (1 - cfg.max_loss_pct/100)
    rr = cfg.gross_target_pct / cfg.max_loss_pct
    if confidence < cfg.min_confidence:
        return TradePlan('NO_TRADE',best.name,confidence,p,target,stop,0,'Best setup did not clear confidence gate.',candidates)
    if rr < cfg.min_reward_risk:
        return TradePlan('NO_TRADE',best.name,confidence,p,target,stop,0,'Reward/risk gate failed.',candidates)
    return TradePlan('BUY',best.name,confidence,p,target,stop,cfg.target_net_pct,
        f'{best.name} selected; target is {cfg.target_net_pct:.2f}% net after configured costs.',candidates)

def manage_position(entry, current, config=None):
    cfg = config or RotationConfig()
    if entry <= 0 or current <= 0:
        return TradePlan('NO_TRADE','NONE',0,None,None,None,0,'Invalid price.')
    pnl = (current/entry-1)*100
    # Floating-point prices can land a few ulps below the configured boundary.
    # Treat an economically equal target/stop as hit rather than delaying the exit.
    epsilon = 1e-9
    if pnl + epsilon >= cfg.gross_target_pct:
        return TradePlan('TAKE_PROFIT','ROTATION_EXIT',1,current,current,entry*(1-cfg.max_loss_pct/100),cfg.target_net_pct,
            f'Target reached at {pnl:.2f}% gross. Book profit, then rescan for a fresh strategy.')
    if pnl - epsilon <= -cfg.max_loss_pct:
        return TradePlan('SELL','RISK_EXIT',1,current,None,None,0,
            f'Risk stop reached at {pnl:.2f}%. Exit and block revenge re-entry.')
    return TradePlan('HOLD','POSITION_MANAGEMENT',.60,current,entry*(1+cfg.gross_target_pct/100),entry*(1-cfg.max_loss_pct/100),0,
        f'Position is {pnl:.2f}% gross; target/stop not reached.')
