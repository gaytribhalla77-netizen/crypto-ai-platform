# IQ200 Final Repair + Audit

## Scope
This repair preserves the existing project architecture and trading logic. No rewrite of the trading system was performed.

## Changes made
- Added root `requirements.txt` as the single install entry point. It includes the existing backend requirements plus pytest/pytest-asyncio.
- Added `scripts/verify_environment.py` to fail clearly when required runtime/audit dependencies (including `aiosqlite`) are missing.
- Added `scripts/audit_local.sh` for a repeatable local compile + full-test audit.
- Updated `RUN_ME_FIRST.md` so installation and verification are performed from the project root.
- Kept `.github/workflows/full-audit.yml` as the clean-runner verification path; it installs `backend/requirements.txt`, including `aiosqlite`, before running tests.

## Verification performed in this environment
- Python compileall: PASS
- Existing test suite: 64 PASS, 2 BLOCKED by missing `aiosqlite`
- Attempted `pip install aiosqlite`: BLOCKED because this environment has no DNS/network access.
- Environment preflight: correctly reports missing `aiosqlite` instead of pretending it is installed.

## Why the 2 tests remain blocked
The two idempotency tests intentionally use SQLAlchemy's async SQLite dialect (`sqlite+aiosqlite`). Replacing them with synchronous SQLite or a homemade compatibility layer would change the test target and could create a false PASS. The project already declares `aiosqlite` in `backend/requirements.txt`; the clean GitHub Actions workflow installs it.

## Live-money status
Not certified for real-money execution by this local audit. Before live trading, the clean CI suite must be green and Binance Testnet execution/reconciliation must be verified. Never commit Binance credentials.
