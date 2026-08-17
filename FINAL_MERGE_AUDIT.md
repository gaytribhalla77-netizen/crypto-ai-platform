# IQ200 Merge + Runnable Audit

Date: 2026-08-17

## Scope
This package preserves the existing IQ200 project code and the Expert Knowledge Catalog already present in the uploaded audited build. No application rewrite was performed.

## Merge verification
The uploaded build contains the existing core project paths, including:
- backend/main.py
- backend/opportunity/engine.py
- backend/ai/orchestrator/service.py
- workers/*
- apps/web/*
- tests/*
- backend/knowledge/*
- backend/knowledge/data/expert_knowledge_pack.json

The Expert Knowledge Catalog contains 36 structured rules.

## Local verification
- Python compileall: PASS
- Pytest: 64 PASS, 2 BLOCKED by missing `aiosqlite` in the audit environment
- Blocked tests:
  - tests/trading/test_idempotency.py::test_duplicate_client_request_id_is_rejected
  - tests/trading/test_idempotency.py::test_different_request_ids_both_succeed
- No hard-coded API-key/secret patterns found by the audit scan.
- Live trading remains OFF by default (`LIVE_TRADING=false`).
- The frontend dependencies were not installed in this environment, so a real Next.js production build was not claimed as PASS.

## Important
The project is packaged as a runnable source project, but a completely green end-to-end audit requires installing the declared dependencies (especially `aiosqlite`) and running the frontend dependency install/build in a normal network-enabled environment.

No real Binance credentials are included.
