import os
import sys

# Tests import modules two ways in this codebase:
#   from backend.trading.risk_manager.production import ProductionRiskManager   (test-facing)
#   from trading.risk_manager.production import ProductionRiskManager           (used internally,
#     e.g. inside backend/trading/risk_manager/engine.py)
# The app itself is normally run with `backend/` as the working directory
# (see docs/deployment/LOCAL_SETUP.md), which is why internal modules use the
# second, backend-relative style. To make both import styles resolve under
# pytest without changing every internal import, put both the repo root and
# backend/ on sys.path.
ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(ROOT, "backend")
for p in (ROOT, BACKEND):
    if p not in sys.path:
        sys.path.insert(0, p)
