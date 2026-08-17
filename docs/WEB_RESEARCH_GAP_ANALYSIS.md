# IQ200+ Web Research Gap Analysis — 2026-08-17

The external survey identified several high-value additions for a real trading agent:

1. **Purged/embargoed time-series validation and leakage controls.** Financial time series must not use ordinary random splits; temporal leakage and overlapping labels can inflate results.
2. **Uncertainty-aware decisions.** A point forecast without uncertainty can overstate confidence. The new uncertainty primitive produces mean/std/interval/confidence metadata.
3. **Feature/pattern discovery with minimum support.** Strategy research should search for repeatable conditional patterns instead of only evaluating hand-written strategies.
4. **Data lineage and point-in-time reproducibility.** Economic data can be revised; Trading Economics explicitly documents point-in-time snapshots and revised values. The agent now fingerprints datasets and records source/timeframe/timestamps.
5. **Execution-quality telemetry.** Slippage, fill ratio and latency must be measured from real execution evidence rather than assumed.
6. **Trading circuit breakers.** Stale data, broker outage, abnormal spreads, drawdown breaches, model drift and unresolved order states must be able to block new trades.
7. **Event-impact measurement.** Macro surprise and post-release market response should become measurable evidence rather than narrative labels.
8. **Deterministic audit/replay fingerprints.** Every important decision/event should be replayable and attributable to a stable event/payload hash.

These additions complement, rather than replace, the existing risk engine, multi-agent council, memory, market-twin, broker adapters and certification gates.

## Important research conclusions

- No public survey can establish that IQ200 is the world's first trading agent. The defensible claim is architectural differentiation.
- Real broker connectivity and test/sandbox execution are different from proof of production reliability.
- Backtest performance is not proof of live performance; the project therefore keeps external-data, paper-trading and broker-certification gates explicit.
- OWASP API Security Top 10 should be treated as a baseline, including authorization, resource consumption, SSRF, security misconfiguration, inventory management and unsafe third-party API consumption.
