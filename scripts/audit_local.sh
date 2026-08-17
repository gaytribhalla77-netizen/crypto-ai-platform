#!/usr/bin/env bash
set -euo pipefail
python scripts/verify_environment.py
python -m compileall -q backend workers tests conftest.py
python -m pytest -q
