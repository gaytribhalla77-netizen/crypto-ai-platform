import os, hashlib, hmac, time
import jwt
from core.config import settings


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return salt.hex() + ":" + digest.hex()

def verify_password(password: str, stored: str) -> bool:
    salt_hex, digest_hex = stored.split(":")
    salt = bytes.fromhex(salt_hex)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return hmac.compare_digest(digest.hex(), digest_hex)


def create_access_token(user_id: int, is_admin: bool = False, token_type: str = 'access') -> str:
    now = int(time.time())
    payload = {
        "sub": str(user_id),
        "is_admin": bool(is_admin),
        "type": token_type,
        "iat": now,
        "exp": now + settings.access_token_minutes * 60,
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def decode_access_token(token: str) -> dict:
    # Raises jwt.PyJWTError (expired, invalid signature, malformed) on failure.
    # Callers must treat any exception as "unauthenticated", not log the user in anyway.
    return jwt.decode(token, settings.secret_key, algorithms=["HS256"])


def create_preauth_token(user_id: int, is_admin: bool = False) -> str:
    return create_access_token(user_id, is_admin, token_type='preauth')
