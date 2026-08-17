from iq200_plus.purged_validation import purged_walk_forward, leakage_check
from iq200_plus.uncertainty import estimate
from iq200_plus.feature_discovery import discover
from iq200_plus.data_lineage import fingerprint
from iq200_plus.execution_quality import measure
from iq200_plus.circuit_breakers import TradingCircuitBreaker
from iq200_plus.event_impact import measure as event_measure
from iq200_plus.replay import record

def test_purged_folds_no_leakage():
    folds=purged_walk_forward(100,5,purge=2,embargo=3)
    assert len(folds)==5
    assert all(leakage_check(f.train,f.test,f.embargoed) for f in folds)

def test_uncertainty():
    u=estimate([1,2,3,4,5])
    assert u.std>0 and u.lower<u.mean<u.upper

def test_discovery():
    rows=[{"a":True,"b":False,"return":1.0}]*25+[{'a':False,'b':True,'return':-1.0}]*25
    p=discover(rows,['a','b'],20)
    assert p and p[0].conditions==('a',)

def test_lineage_is_stable():
    rows=[{"timestamp":1,"x":2}]
    assert fingerprint(rows)==fingerprint(rows)

def test_execution_quality_and_breaker():
    q=measure(100,100.1,'BUY',10,9,25)
    assert q.slippage_bps>0 and q.fill_ratio==.9
    b=TradingCircuitBreaker(); b.state.stale_data=True
    assert b.blocked()

def test_event_and_replay():
    e=event_measure(110,100,0.0,0.02,0.01,0.03)
    assert e.surprise==.1 and e.direction=='UP'
    r=record('x','DECISION',{'a':1},1)
    assert len(r.payload_hash)==64
