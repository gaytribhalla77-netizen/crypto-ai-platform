from ai.regime import detect_regime
from ai.adversarial import challenge_trade
from ai.counterfactual import evaluate_actions
from ai.data_quality import assess_market_data
from ai.calibration import brier_score, calibrate_confidence
from portfolio.advanced_risk import correlation, portfolio_metrics
from backtesting.engine import run_backtest
from strategy_lab import StrategyLab

def test_regime_and_quality():
    closes=[100+i*0.5 for i in range(40)]
    r=detect_regime(closes)
    assert r.name in {"TREND_UP","RANGE","HIGH_VOLATILITY","LOW_VOLATILITY_RANGE","TREND_DOWN"}
    assert assess_market_data(120,40)["safe"]

def test_adversarial_blocks_unsafe_trade():
    c=challenge_trade("BUY",80,{"risk":"HIGH"},{"name":"TREND_UP"},{"safe":True})
    assert not c.approved

def test_counterfactual_has_four_actions():
    out=evaluate_actions(100,0.03,0.01,0.005)
    assert {x["action"] for x in out}=={"BUY","SELL","WAIT","NO_TRADE"}

def test_backtest_accounts_for_costs():
    r=run_backtest([100,102,104,100,105])
    assert r.trades >= 1
    assert r.fees_paid > 0

def test_strategy_lab_and_risk_metrics():
    closes=[100+i*0.2 for i in range(60)]
    c=StrategyLab().evaluate(closes)
    assert len(c)==2
    assert -1 <= correlation([1,2,3],[1,2,3]) <= 1
    m=portfolio_metrics([-.02,.01,.03,-.01])
    assert "cvar_pct" in m

def test_calibration():
    b=brier_score([.9,.1],[1,0])
    assert b < .02
    assert calibrate_confidence(90,b) <= 90
