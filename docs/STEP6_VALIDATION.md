# Step 6 — Paper/Testnet Validation

## What is now automated

- `backend/certification/step6_runner.py` runs the deterministic 10,000-bar validation.
- Every run writes append-only JSONL audit events to `artifacts/step6/validation.jsonl`.
- The latest certification is written to `artifacts/step6/certification.json` with `PASS`/`FAIL` and every gate result.
- `.github/workflows/step6-validation.yml` runs the validation on demand and every 30 minutes and uploads the audit artifacts.

## Run locally

```bash
python -m backend.certification.step6_runner --mode paper --bars 10000
```

Testnet mode is deliberately fail-closed and currently uses the same non-ordering certification path. It does **not** submit real-money orders. A sandbox exchange adapter can be wired in later behind explicit credentials and a separate order-safety gate.

## Completion rule

Step 6 is `PASS` only when all deterministic gates pass:

1. deterministic backtest produces trades
2. all tracked metrics are finite
3. drawdown is bounded to 0–100%
4. fees and slippage are non-negative
5. 10,000 bars complete within the performance budget

The certification JSON is the machine-readable source of truth for the run.
