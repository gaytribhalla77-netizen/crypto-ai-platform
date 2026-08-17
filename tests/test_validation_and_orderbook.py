from ai.validation import walk_forward, monte_carlo_trade_sequence, model_drift

def test_validation_primitives():
    closes=[100+i*.1 for i in range(100)]
    w=walk_forward(closes,folds=4)
    assert w['status']=='OK'
    m=monte_carlo_trade_sequence([.01,-.005,.002],simulations=100)
    assert m['simulations']==100
    assert model_drift([.01,.01,.02],[.01,.011])['status'] in {'STABLE','DRIFT'}
