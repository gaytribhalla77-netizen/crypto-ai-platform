"""Step 6 paper/testnet validation runner.

Paper mode is fully offline. Testnet mode adds a read-only authenticated
Binance Testnet connectivity check (account + exchange filters) and never
submits an order. Real execution remains outside automated certification.
"""
from __future__ import annotations

import argparse
import json
import os
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from backtesting.engine import run_backtest
except ModuleNotFoundError:
    from backend.backtesting.engine import run_backtest

try:
    from certification.step6 import run_offline_step6_gates, Step6Gate
except ModuleNotFoundError:
    from backend.certification.step6 import run_offline_step6_gates, Step6Gate

try:
    from certification.testnet_connectivity import validate_testnet
except ModuleNotFoundError:
    from backend.certification.testnet_connectivity import validate_testnet


AUDIT_DIR = Path(os.getenv("STEP6_AUDIT_DIR", "artifacts/step6"))
AUDIT_FILE = AUDIT_DIR / "validation.jsonl"
CERT_FILE = AUDIT_DIR / "certification.json"


@dataclass
class AuditEvent:
    timestamp: str
    run_id: str
    event: str
    mode: str
    payload: dict[str, Any]


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def append_audit(run_id: str, event: str, mode: str, payload: dict[str, Any]) -> None:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    record = AuditEvent(_utc(), run_id, event, mode, payload)
    with AUDIT_FILE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(asdict(record), sort_keys=True) + "\n")


def certify(run_id: str, mode: str, gates: list[Any], duration_s: float) -> dict[str, Any]:
    passed = bool(gates) and all(g.passed for g in gates)
    result = {
        "schema_version": 2,
        "run_id": run_id,
        "timestamp": _utc(),
        "mode": mode,
        "status": "PASS" if passed else "FAIL",
        "duration_s": round(duration_s, 6),
        "gates": [asdict(g) for g in gates],
    }
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    CERT_FILE.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    append_audit(run_id, "certification", mode, result)
    return result


async def run_async(mode: str = "paper", bars: int = 10_000) -> dict[str, Any]:
    if mode not in {"paper", "testnet"}:
        raise ValueError("mode must be paper or testnet")

    run_id = datetime.now(timezone.utc).strftime("step6-%Y%m%dT%H%M%SZ")
    started = time.perf_counter()
    append_audit(run_id, "run_started", mode, {"bars": bars})

    gates = run_offline_step6_gates() if bars == 10_000 else []
    append_audit(run_id, "offline_gates", mode, {"gates": [asdict(g) for g in gates]})

    if mode == "testnet":
        try:
            symbol = os.getenv("TESTNET_SYMBOL", "BTCUSDT")
            connectivity = await validate_testnet(symbol)
            gates.append(Step6Gate("binance_testnet_connectivity", True, f"authenticated; symbol={symbol.upper()}"))
            append_audit(run_id, "testnet_connectivity", mode, connectivity)
        except Exception as exc:
            gates.append(Step6Gate("binance_testnet_connectivity", False, str(exc)))
            append_audit(run_id, "testnet_connectivity_failed", mode, {"error": str(exc)})

    duration = time.perf_counter() - started
    result = certify(run_id, mode, gates, duration)
    append_audit(run_id, "run_finished", mode, {"status": result["status"]})
    return result


def run(mode: str = "paper", bars: int = 10_000) -> dict[str, Any]:
    import asyncio
    return asyncio.run(run_async(mode, bars))


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Step 6 paper/testnet certification")
    parser.add_argument("--mode", choices=("paper", "testnet"), default="paper")
    parser.add_argument("--bars", type=int, default=10_000)
    args = parser.parse_args()
    result = run(args.mode, args.bars)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
