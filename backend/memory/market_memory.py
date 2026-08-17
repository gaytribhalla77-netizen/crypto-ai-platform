from __future__ import annotations
from dataclasses import dataclass, asdict
from math import sqrt
import json
from pathlib import Path


@dataclass
class MemoryRecord:
    symbol: str
    timestamp: float
    regime: str
    action: str
    confidence: float
    features: dict
    outcome_return: float | None = None
    outcome_correct: bool | None = None
    reason: str = ''


class MarketMemory:
    """Durable JSONL market memory isolated by authenticated user.

    Each instance is bound to exactly one positive integer user_id. Records are
    stored under ``data/market_memory/users/<user_id>.jsonl`` so one user's
    decision history can never be returned by another user's similarity query.
    The legacy shared ``data/market_memory.jsonl`` file is intentionally not
    read or written; it was an unscoped security boundary.
    """

    BASE_DIR = Path('data/market_memory/users')
    MAX_RECORD_BYTES = 64 * 1024
    MAX_FILE_BYTES = 10 * 1024 * 1024

    def __init__(self, user_id: int):
        try:
            user_id = int(user_id)
        except (TypeError, ValueError):
            raise ValueError('user_id must be a positive integer')
        if user_id <= 0:
            raise ValueError('user_id must be a positive integer')
        self.user_id = user_id
        self.path = self.BASE_DIR / f'{user_id}.jsonl'

    def add(self, record: MemoryRecord):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        encoded = (json.dumps(asdict(record), sort_keys=True, separators=(',', ':')) + '\n').encode('utf-8')
        if len(encoded) > self.MAX_RECORD_BYTES:
            raise ValueError('memory record is too large')
        current_size = self.path.stat().st_size if self.path.exists() else 0
        if current_size + len(encoded) > self.MAX_FILE_BYTES:
            raise ValueError('per-user memory storage limit reached')
        with self.path.open('ab') as f:
            f.write(encoded)

    def all(self):
        try:
            with self.path.open(encoding='utf-8') as f:
                return [json.loads(x) for x in f if x.strip()]
        except FileNotFoundError:
            return []

    @staticmethod
    def _vector(features):
        keys = sorted(features)
        return [(str(features[k]), k) for k in keys]

    def similar(self, features: dict, symbol: str | None = None, limit: int = 20):
        target = self._vector(features)
        rows = []
        for r in self.all():
            if symbol and r.get('symbol') != symbol:
                continue
            vec = self._vector(r.get('features', {}))
            shared = {(k, v) for v, k in target} & {(k, v) for v, k in vec}
            denom = sqrt(max(1, len(target)) * max(1, len(vec)))
            score = len(shared) / denom
            rows.append((score, r))
        rows.sort(key=lambda x: x[0], reverse=True)
        return [{'similarity': round(s, 6), **r} for s, r in rows[:limit]]

    def digest(self, features, symbol=None):
        matches = self.similar(features, symbol, 50)
        outcomes = [m['outcome_return'] for m in matches if m.get('outcome_return') is not None]
        return {
            'matches': len(matches),
            'avg_return': sum(outcomes) / len(outcomes) if outcomes else None,
            'records': matches[:10],
        }
