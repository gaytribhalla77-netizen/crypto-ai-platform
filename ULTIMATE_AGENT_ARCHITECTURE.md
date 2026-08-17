# Ultimate Market Agent Architecture

This build adds five major layers without enabling unsafe autonomous live trading:

1. **Validated Self-Learning Loop** — proposes hypotheses, backtests, walk-forward validates, stress-tests, and only promotes candidates to paper-trading eligibility. It never edits live rules automatically.
2. **Multi-Agent Trading Council** — technical, news, ML, regime, order-flow, and macro agents vote; regime can veto.
3. **Digital Market Twin** — Monte-Carlo counterfactual simulation compares BUY/SELL/WAIT outcomes and drawdown risk.
4. **Macro + Order-Flow Intelligence** — provider-neutral economic surprise/risk analysis and depth/imbalance analysis.
5. **FX Sandbox Execution** — provider-neutral sandbox broker contract that exercises the order/reconciliation path without live credentials.

## Safety boundary
No live broker credentials are invented. No component can claim guaranteed profitability. No self-learning candidate can modify live strategy code; promotion stops at paper-candidate status until separately approved and audited.
