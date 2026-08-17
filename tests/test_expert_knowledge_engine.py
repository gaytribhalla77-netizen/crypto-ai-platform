import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__),"..","backend"))
from knowledge.engine import TradingKnowledgeEngine
from knowledge.validator import StrategyValidator

def test_knowledge_engine_has_failure_conditions():
    k=TradingKnowledgeEngine()
    assert len(k.items) >= 6
    assert all(i.failure_conditions for i in k.items)

def test_high_impact_news_blocks_setup():
    k=TradingKnowledgeEngine()
    r=k.evaluate_setup(market={}, news={"market_impact":{"severity":"HIGH"}}, risk={"status":"PASS"})
    assert r["status"]=="WAIT"
    assert "market_moving_news" in r["blockers"]

def test_unknown_news_blocks_setup():
    k=TradingKnowledgeEngine()
    r=k.evaluate_setup(market={}, news={"market_impact":{"severity":"LOW","status":"CONFLICTING"}}, risk={"status":"PASS"})
    assert r["status"]=="WAIT"
    assert "news_uncertainty" in r["blockers"]

def test_unvalidated_strategy_is_quarantined():
    k=TradingKnowledgeEngine()
    r=k.evaluate_setup(market={}, news={"market_impact":{"severity":"LOW"}}, risk={"status":"PASS"}, strategy={"validation_status":"CANDIDATE"})
    assert r["status"]=="WAIT"

def test_lessons_never_auto_promote():
    k=TradingKnowledgeEngine()
    r=k.quarantine_lesson({"pattern":"x","result":1})
    assert r["status"]=="QUARANTINED"
    assert r["requires_backtest"] and r["requires_out_of_sample"] and r["requires_testnet"]

def test_strategy_validator_rejects_missing_evidence():
    r=StrategyValidator().validate("x", {})
    assert r["status"]=="QUARANTINED"
    assert "missing:" in r["reasons"][0]

def test_strategy_validator_requires_costs():
    m={"sample_size":1000,"return_pct":20,"max_drawdown_pct":10,"win_rate":.6,"profit_factor":1.4,
       "fees_modelled":False,"slippage_modelled":False,"lookahead_checked":True}
    r=StrategyValidator().validate("x",m)
    assert r["status"]=="QUARANTINED"
