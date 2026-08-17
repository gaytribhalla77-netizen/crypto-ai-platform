import hashlib
import json

def request_key(user_id: int, symbol: str, side: str, amount_usdt: float, client_request_id: str):
    payload = {
        "user_id": user_id,
        "symbol": symbol.upper(),
        "side": side.upper(),
        "amount_usdt": round(float(amount_usdt), 8),
        "client_request_id": client_request_id,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
