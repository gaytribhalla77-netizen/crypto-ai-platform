import jwt
from dataclasses import dataclass
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select

from auth.security import decode_access_token
from database.session import SessionLocal
from database.models import User

_bearer = HTTPBearer(auto_error=False)


@dataclass
class CurrentUser:
    id: int
    is_admin: bool


async def get_db_session():
    async with SessionLocal() as session:
        yield session


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    session=Depends(get_db_session),
) -> CurrentUser:
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token.")
    try:
        payload = decode_access_token(credentials.credentials)
        if payload.get('type', 'access') != 'access':
            raise ValueError('preauth token is not an access token')
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token.")

    user_id = int(payload["sub"])
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        # Token was validly signed but the user no longer exists — deny, don't trust the claim alone.
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User no longer exists.")
    return CurrentUser(id=user.id, is_admin=user.is_admin)


async def require_admin(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if not user.is_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin privileges required.")
    return user
