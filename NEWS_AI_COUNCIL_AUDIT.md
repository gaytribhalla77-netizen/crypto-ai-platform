# News + AI Council Audit

## Requirement implemented
Before a trading recommendation is considered, the intelligence layer now separates:
- technical evidence
- fresh relevant news
- market-moving news impact and severity
- historical context from chronological prior observations
- model evidence when available
- regime / macro / order-flow context
- sentiment context
- adversarial contradiction handling

News impact is not treated as a simple positive/negative headline score. Recency and market-moving terms influence severity. Critical/high-impact news is surfaced separately from sentiment.

Historical context explicitly refuses to produce a directional result when the sample is insufficient.

The council records historical and sentiment votes and marks contradictory BUY/SELL evidence. The chief judge returns WAIT when contradiction or a hard regime veto is active.

## Safety principle
No component guarantees profit. The intelligence layer is advisory evidence; the canonical risk firewall remains authoritative for execution.

## Verification
Focused intelligence/live safety tests: 28 passed.
Full suite: 50 passed, 2 environment-blocked because `aiosqlite` is unavailable in this audit environment.

The two blocked tests are the existing DB idempotency tests. They are not counted as passes.
