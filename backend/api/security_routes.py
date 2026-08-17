from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from auth.dependencies import get_current_user, get_db_session, CurrentUser
from database.models import SecuritySetting, CredentialVault as CredentialVaultModel
from security.totp import new_secret, verify
from security.vault import CredentialVault
from security.kill_switch import set_kill_switch, is_killed
from security.reconciliation import reconcile_trade
from database.models import Trade
from exchanges.binance.client import BinanceClient
from core.config import settings

router=APIRouter(prefix='/api/security', tags=['security'])

class TotpCode(BaseModel): code:str
class CredentialPayload(BaseModel): provider:str; credentials:dict

@router.post('/2fa/setup')
async def setup_2fa(user:CurrentUser=Depends(get_current_user), session=Depends(get_db_session)):
    secret=new_secret(); vault=CredentialVault(); enc=vault.encrypt({'secret':secret})
    row=(await session.execute(select(SecuritySetting).where(SecuritySetting.user_id==user.id))).scalar_one_or_none()
    if row is None: row=SecuritySetting(user_id=user.id); session.add(row)
    row.totp_secret_encrypted=enc; row.totp_enabled=False
    await session.commit()
    return {'secret':secret,'otpauth':'otpauth://totp/AI-Trading:user-'+str(user.id)+'?secret='+secret+'&issuer=AI-Trading','enabled':False}

@router.post('/2fa/enable')
async def enable_2fa(body:TotpCode,user:CurrentUser=Depends(get_current_user),session=Depends(get_db_session)):
    row=(await session.execute(select(SecuritySetting).where(SecuritySetting.user_id==user.id))).scalar_one_or_none()
    if not row or not row.totp_secret_encrypted: raise HTTPException(400,'2FA setup required first.')
    secret=CredentialVault().decrypt(row.totp_secret_encrypted)['secret']
    if not verify(secret,body.code): raise HTTPException(401,'Invalid 2FA code.')
    row.totp_enabled=True; await session.commit(); return {'enabled':True}

@router.post('/2fa/disable')
async def disable_2fa(body:TotpCode,user:CurrentUser=Depends(get_current_user),session=Depends(get_db_session)):
    row=(await session.execute(select(SecuritySetting).where(SecuritySetting.user_id==user.id))).scalar_one_or_none()
    if not row or not row.totp_enabled: return {'enabled':False}
    secret=CredentialVault().decrypt(row.totp_secret_encrypted)['secret']
    if not verify(secret,body.code): raise HTTPException(401,'Invalid 2FA code.')
    row.totp_enabled=False; await session.commit(); return {'enabled':False}

@router.get('/status')
async def security_status(user:CurrentUser=Depends(get_current_user),session=Depends(get_db_session)):
    row=(await session.execute(select(SecuritySetting).where(SecuritySetting.user_id==user.id))).scalar_one_or_none()
    return {'totp_enabled': bool(row and row.totp_enabled), 'kill_switch':await is_killed(session,user.id)}

@router.post('/kill-switch')
async def kill_switch(enabled:bool,user:CurrentUser=Depends(get_current_user),session=Depends(get_db_session)):
    await set_kill_switch(session,user.id,enabled); return {'kill_switch':enabled}

@router.post('/credentials')
async def save_credentials(body:CredentialPayload,user:CurrentUser=Depends(get_current_user),session=Depends(get_db_session)):
    provider = body.provider.strip().lower()
    if provider not in {"binance", "oanda"}:
        raise HTTPException(400, "Supported credential providers are binance and oanda.")
    if provider == "binance" and not body.credentials.get("api_key") or provider == "binance" and not body.credentials.get("api_secret"):
        raise HTTPException(400, "Binance credentials require api_key and api_secret.")
    if provider == "oanda" and not (body.credentials.get("api_token") or body.credentials.get("token")) or provider == "oanda" and not body.credentials.get("account_id"):
        raise HTTPException(400, "OANDA credentials require api_token (or token) and account_id.")
    # Secret values are never returned; they are encrypted before persistence.
    enc=CredentialVault().encrypt(body.credentials)
    row=CredentialVaultModel(user_id=user.id,provider=provider,encrypted_payload=enc)
    session.add(row); await session.commit()
    return {'stored':True,'provider':row.provider}

@router.post('/reconcile/{trade_id}')
async def reconcile(trade_id:int,user:CurrentUser=Depends(get_current_user),session=Depends(get_db_session)):
    trade=(await session.execute(select(Trade).where(Trade.id==trade_id,Trade.user_id==user.id))).scalar_one_or_none()
    if not trade: raise HTTPException(404,'Trade not found.')
    try:
        creds = await CredentialVault().get_provider_credentials(session, user.id, "binance")
        exchange = BinanceClient(creds.get("api_key"), creds.get("api_secret"), testnet=not settings.live_trading)
    except RuntimeError:
        raise HTTPException(409, "Binance credentials are not configured for this user.")
    return await reconcile_trade(session,trade,exchange)
