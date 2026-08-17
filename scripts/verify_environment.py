"""Preflight dependency check for IQ200.

This does not change trading behavior. It only tells the operator whether
all runtime/audit dependencies are installed before starting the application.
"""
from __future__ import annotations

import importlib.util
import sys

REQUIRED = {
    "fastapi": "fastapi",
    "sqlalchemy": "sqlalchemy",
    "aiosqlite": "aiosqlite",
    "websockets": "websockets",
    "pytest": "pytest",
    "pytest_asyncio": "pytest-asyncio",
}

missing = [pkg for module, pkg in REQUIRED.items() if importlib.util.find_spec(module) is None]
if missing:
    print("MISSING: " + ", ".join(missing))
    print("Install with: python -m pip install -r requirements.txt")
    sys.exit(2)

print("Environment preflight: PASS")
print("All required backend/test dependencies are installed.")
