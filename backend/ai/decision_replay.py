from __future__ import annotations
import json, hashlib

def canonical_hash(payload:dict)->str:
    raw=json.dumps(payload,sort_keys=True,separators=(',',':')).encode()
    return hashlib.sha256(raw).hexdigest()

def replay_record(payload:dict):
    return {'input_hash':canonical_hash(payload.get('input',{})),'decision_hash':canonical_hash(payload.get('decision',{})),'replayable':bool(payload.get('input') is not None and payload.get('decision') is not None)}
