# IQ200 Expert Knowledge Engine Audit

## Scope
Added a versioned Trading Knowledge Engine and strategy-promotion gate to the Binance real-time + AI Council build.

### Included
- Core trading principles with explicit conditions and failure conditions.
- Evidence/source metadata and review timestamps.
- Knowledge search interface.
- Market/news/risk knowledge gate.
- High/critical or uncertain market-moving news blocks eligibility.
- Strategy validation requiring sample size, costs, slippage and lookahead checks.
- High drawdown quarantine.
- New lessons are quarantined and cannot auto-promote to production.
- Council service now exposes `knowledge_gate` and cannot mark a setup trade-ready unless the knowledge gate is eligible.

## Audit Results
- Pytest: **61 passed, 2 environment-blocked**
- Blocked tests: two SQLite async idempotency tests; `aiosqlite` is unavailable in this audit environment.
- Python compilation: **PASS**
- New expert-knowledge tests: **7/7 PASS**
- Existing regression/live/news/council tests: **PASS** except the two dependency-blocked tests.

## Important limitation
This engine is an evidence framework, not a claim of perfect trading knowledge or guaranteed profitability. Production strategy promotion still requires historical backtest, out-of-sample validation, Testnet validation and live risk gates.
