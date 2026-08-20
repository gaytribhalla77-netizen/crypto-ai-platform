from __future__ import annotations

import asyncio
import logging
import os
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable

logger = logging.getLogger("security.continuous_self_audit")


@dataclass(frozen=True)
class SelfFinding:
    rule: str
    severity: str
    path: str
    message: str
    remediation: str


_SECRET_PATTERNS = (
    re.compile(r"(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*[\"'][^\"']{12,}[\"']"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
)
_DANGEROUS_PATTERNS = (
    (re.compile(r"(?i)subprocess\.(run|Popen|call)\([^\n]*shell\s*=\s*True"), "SEC-001", "high", "Review shell execution; prefer argument arrays and avoid shell=True.") ,
    (re.compile(r"(?i)verify\s*=\s*False"), "SEC-002", "medium", "Do not disable TLS certificate verification in production paths."),
    (re.compile(r"(?i)pickle\.(load|loads)\("), "SEC-003", "medium", "Do not deserialize untrusted pickle data; use a safe structured format."),
)


class ContinuousSelfAuditor:
    """Cheap, repeatable, non-destructive checks against this service's source tree.

    It never attacks external systems, changes application code automatically,
    executes discovered payloads, or handles secrets as test data. Findings are
    advisory and should be triaged before any remediation.
    """

    def __init__(self, root: str | Path | None = None, interval_seconds: int = 900):
        self.root = Path(root or Path(__file__).resolve().parents[2])
        self.interval_seconds = max(60, int(interval_seconds))
        self._stop = asyncio.Event()

    def _files(self) -> Iterable[Path]:
        allowed = {".py", ".ts", ".tsx", ".js", ".jsx", ".json", ".yml", ".yaml", ".toml"}
        ignored = {".git", "node_modules", ".next", "__pycache__", ".venv", "venv"}
        for path in self.root.rglob("*"):
            if path.is_file() and path.suffix.lower() in allowed and not any(part in ignored for part in path.parts):
                yield path

    def scan_once(self) -> dict:
        findings: list[SelfFinding] = []
        for path in self._files():
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            rel = str(path.relative_to(self.root))
            if any(p.search(text) for p in _SECRET_PATTERNS) and not rel.endswith(".env.example"):
                findings.append(SelfFinding("SEC-000", "high", rel, "Possible hard-coded secret/token pattern detected.", "Move credentials to the secret manager/environment and rotate any real exposed credential."))
            for pattern, rule, severity, remediation in _DANGEROUS_PATTERNS:
                if pattern.search(text):
                    findings.append(SelfFinding(rule, severity, rel, f"Potential risky pattern matched: {pattern.pattern}", remediation))
            if "DEBUG = True" in text or "debug=True" in text:
                findings.append(SelfFinding("SEC-004", "medium", rel, "Debug mode appears enabled in source/configuration.", "Disable debug mode outside local development."))

        counts = {level: sum(f.severity == level for f in findings) for level in ("critical", "high", "medium", "low", "info")}
        return {"findings": [asdict(f) for f in findings], "summary": counts, "checked_at": asyncio.get_running_loop().time()}

    async def run_forever(self, callback=None) -> None:
        while not self._stop.is_set():
            try:
                result = await asyncio.to_thread(self.scan_once)
                if callback:
                    await callback(result) if asyncio.iscoroutinefunction(callback) else callback(result)
                logger.info("Continuous security self-audit: %s", result["summary"])
            except Exception:
                logger.exception("Continuous security self-audit failed")
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=self.interval_seconds)
            except asyncio.TimeoutError:
                pass

    async def stop(self) -> None:
        self._stop.set()
