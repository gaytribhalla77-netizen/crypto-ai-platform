import time
from collections import defaultdict, deque
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import select
from auth.security import hash_password, verify_password, create_access_token, create_preauth_token, decode_access_token
from auth.dependencies import get_db_session
from database.models import User, SecuritySetting
from security.vault import CredentialVault
from security.totp import verify as verify_totp

router = APIRouter(prefix="/api/auth", tags=["auth"])
_attempts: dict[str, deque[float]] = defaultdict(deque)
_WINDOW = 300
_MAX_FAILURES = 8

class Credentials(BaseModel):
    email: str
    password: str

class TwoFactorLogin(BaseModel):
    preauth_token: str
    code: str

def _check_rate_limit(key: str):
    now = time.time(); q = _attempts[key]
    while q and now - q[0] > _WINDOW: q.popleft()
    if len(q) >= _MAX_FAILURES:
        raise HTTPException(429, "Too many failed login attempts. Try again later.")

def _record_failure(key: str): _attempts[key].append(time.time())
def _clear_failures(key: str): _attempts.pop(key, None)

@router.post("/register")
async def register(body: Credentials, session=Depends(get_db_session)):
    email = body.email.strip().lower()
    if len(body.password) < 12:
        raise HTTPException(400, "Password must be at least 12 characters.")
    existing = await session.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(409, "Email already registered.")
    user = User(email=email, password_hash=hash_password(body.password), is_admin=False)
    session.add(user)
    await session.commit(); await session.refresh(user)
    return {"access_token": create_access_token(user.id, user.is_admin), "token_type": "bearer"}

@router.post("/login")
async def login(body: Credentials, session=Depends(get_db_session)):
    key = body.email.strip().lower(); _check_rate_limit(key)
    result = await session.execute(select(User).where(User.email == key))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(body.password, user.password_hash):
        _record_failure(key)
        raise HTTPException(401, "Invalid email or password.")
    _clear_failures(key)
    setting=(await session.execute(select(SecuritySetting).where(SecuritySetting.user_id==user.id))).scalar_one_or_none()
    if setting and setting.totp_enabled:
        return {"requires_2fa":True,"preauth_token":create_preauth_token(user.id,user.is_admin),"token_type":"preauth"}
    return {"access_token": create_access_token(user.id, user.is_admin), "token_type": "bearer"}

@router.post('/login/2fa')
async def login_2fa(body:TwoFactorLogin, session=Depends(get_db_session)):
    try:
        payload=decode_access_token(body.preauth_token)
        if payload.get('type')!='preauth': raise ValueError('not preauth')
        user_id=int(payload['sub'])
    except Exception:
        raise HTTPException(401,'Invalid or expired pre-authentication token.')
    user=(await session.execute(select(User).where(User.id==user_id))).scalar_one_or_none()
    setting=(await session.execute(select(SecuritySetting).where(SecuritySetting.user_id==user_id))).scalar_one_or_none()
    if not user or not setting or not setting.totp_enabled: raise HTTPException(401,'2FA is not enabled for this account.')
    secret=CredentialVault().decrypt(setting.totp_secret_encrypted)['secret']
    if not verify_totp(secret,body.code): raise HTTPException(401,'Invalid 2FA code.')
    return {'access_token':create_access_token(user.id,user.is_admin),'token_type':'bearer'}
