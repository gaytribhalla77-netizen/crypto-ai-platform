from ai.pattern_discovery import discover_patterns
from ai.calibrated_council import IndependentCouncil
from ai.council import IQ200Council
from market.orderflow_advanced import analyze_sequence
from memory.market_memory import MarketMemory, MemoryRecord
from ai.decision_replay import replay_record


def test_pattern_discovery_real_labels():
    rows=[]
    for i in range(80):
        high = i < 40
        positive = (i < 35) if high else (i < 50)
        rows.append({'trend_strength':1 if high else -1,'volatility':0.1,'volatility_median':0.2,'orderflow_imbalance':0.2 if high else -0.2,'macro_surprise':0.3 if high else -0.3,'news_score':0.2 if high else -0.2,'spread':0.01,'spread_median':0.02,'forward_return':0.01 if positive else -0.001})
    patterns=discover_patterns(rows,min_support=20)
    assert patterns and patterns[0]['support']>=20


def test_council_full_debate():
    payload={'technical':{'score':1,'trend':'BULLISH'},'news':{'sentiment_score':.4},'risk':{},'regime':{'volatility':.02,'regime':'BULL'},'ml':{'probability_up':.7},'orderflow':{'imbalance':.2},'macro':{'risk_score':.1,'surprise_score':.3}}
    out=IQ200Council().deliberate_full(payload)
    assert {'bull_case','bear_case','adversarial_challenge','chief_judge'}<=out.keys()


def test_orderflow_sequence():
    snaps=[]
    for i in range(5): snaps.append({'bids':[[100,100-i*30]],'asks':[[101,50+i*20]]})
    out=analyze_sequence(snaps)
    assert out['samples']==5 and 'spoofing_like_anomaly' in out


def test_memory_similarity(tmp_path):
    # Fix: MarketMemory's constructor changed from `MarketMemory(path_str)`
    # to `MarketMemory(user_id: int)` when memory storage was made
    # per-user (see AUDIT_FINDINGS_ROUND1.md / ROUND2_FIX_RESULTS.txt).
    # This test still needs to write into a throwaway tmp_path instead of
    # the real data/market_memory/users/ directory, so it swaps BASE_DIR
    # for the duration of the test -- same pattern used in
    # tests/regression_round2_stdlib.py::test_memory_isolation.
    old_base_dir = MarketMemory.BASE_DIR
    MarketMemory.BASE_DIR = tmp_path
    try:
        m = MarketMemory(101)
        m.add(MemoryRecord('EUR_USD', 1, 'BULL', 'BUY', 80, {'regime': 'BULL', 'imbalance': 'HIGH'}, .01, True))
        out = m.digest({'regime': 'BULL', 'imbalance': 'HIGH'}, 'EUR_USD')
        assert out['matches'] == 1 and out['avg_return'] == .01
    finally:
        MarketMemory.BASE_DIR = old_base_dir


def test_replay_hash():
    out=replay_record({'input':{'x':1},'decision':{'action':'WAIT'}})
    assert len(out['input_hash'])==64 and out['replayable']
