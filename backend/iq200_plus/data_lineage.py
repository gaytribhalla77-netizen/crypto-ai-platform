import hashlib, json, time
from dataclasses import dataclass, asdict

@dataclass(frozen=True)
class DataLineage:
    source: str
    symbol: str
    timeframe: str
    first_ts: int | None
    last_ts: int | None
    row_count: int
    content_hash: str
    retrieved_at: float

def fingerprint(rows: list[dict]) -> str:
    payload=json.dumps(rows,sort_keys=True,separators=(",",":"),default=str).encode()
    return hashlib.sha256(payload).hexdigest()

def make_lineage(source,symbol,timeframe,rows):
    ts=[r.get("timestamp") for r in rows if r.get("timestamp") is not None]
    return DataLineage(source,symbol,timeframe,min(ts) if ts else None,max(ts) if ts else None,len(rows),fingerprint(rows),time.time())
