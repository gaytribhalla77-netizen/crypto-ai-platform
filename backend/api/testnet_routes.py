from fastapi import APIRouter, HTTPException, Depends
from exchanges.binance.testnet_client import BinanceTestnetClient
from auth.dependencies import get_current_user, get_db_session
from portfolio.state import PortfolioStateService
from security.vault import CredentialVault
from core.config import settings

router = APIRouter(prefix="/api/testnet", tags=["binance-testnet"])
client = BinanceTestnetClient()

@router.get("/account")
async def testnet_account(user=Depends(get_current_user), session=Depends(get_db_session)):
    try:
        try:
            creds = await CredentialVault().get_provider_credentials(session, user.id, "binance")
            user_client = BinanceTestnetClient(creds.get("api_key"), creds.get("api_secret"))
        except Exception:
            if not settings.single_operator_mode:
                raise
            user_client = client
        return await user_client.account()
    except Exception as e:
        raise HTTPException(status_code=502, detail="Exchange account unavailable.")

@router.post("/order")
async def testnet_order_direct():
    # Intentionally disabled: raw exchange orders bypass the canonical risk,
    # portfolio-state and idempotency pipeline. This route is kept only as an
    # explicit compatibility boundary so old clients fail safely.
    raise HTTPException(410, "Direct testnet orders are disabled. Use /api/v06/testnet/order.")
