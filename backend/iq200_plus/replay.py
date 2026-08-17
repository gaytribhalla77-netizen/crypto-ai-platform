import json, hashlib
from dataclasses import dataclass

@dataclass(frozen=True)
class ReplayRecord:
    event_id: str
    event_type: str
    payload_hash: str
    sequence: int

def record(event_id,event_type,payload,sequence):
    raw=json.dumps(payload,sort_keys=True,separators=(",",":"),default=str).encode()
    return ReplayRecord(event_id,event_type,hashlib.sha256(raw).hexdigest(),sequence)
