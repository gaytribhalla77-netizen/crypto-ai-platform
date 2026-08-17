import base64, hashlib, hmac, secrets, struct, time

def new_secret() -> str:
    return base64.b32encode(secrets.token_bytes(20)).decode().rstrip('=')

def code(secret: str, timestamp: int | None = None, step: int = 30) -> str:
    ts = int(time.time() if timestamp is None else timestamp) // step
    key = base64.b32decode(secret + '=' * ((8-len(secret)%8)%8), casefold=True)
    msg = struct.pack('>Q', ts)
    digest = hmac.new(key, msg, hashlib.sha1).digest()
    offset = digest[-1] & 15
    num = struct.unpack('>I', digest[offset:offset+4])[0] & 0x7fffffff
    return f'{num % 1000000:06d}'

def verify(secret: str, token: str, window: int = 1) -> bool:
    now = int(time.time())
    token = str(token).strip()
    return any(hmac.compare_digest(code(secret, now + i*30), token) for i in range(-window, window+1))
