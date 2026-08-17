# IQ200 — Run This Build

## Backend
1. Copy `.env.example` to `.env`.
2. Keep `LIVE_TRADING=false` and `BINANCE_TESTNET=true` initially.
3. Install all runtime + audit dependencies from the project root:
   `python -m venv .venv`
   activate the environment
   `python -m pip install -r requirements.txt`
4. Verify the environment before starting:
   `python scripts/verify_environment.py`
5. From the project root, run:
   `uvicorn backend.main:app --reload --port 8000`

## Web
1. `cd apps/web`
2. `npm install`
3. `npm run dev`

## Full audit
From the project root, run `pytest -q`. The repository also includes a GitHub Actions workflow at `.github/workflows/full-audit.yml` that installs `aiosqlite` and the complete dependency set on a clean runner before testing/building.

## Verification
From the project root:
`pytest -q`

Do not put Binance secrets in frontend code or commit them to GitHub.
Do not enable live trading until the full test suite is green and Testnet execution/reconciliation has been verified.
