from datetime import datetime, timezone
from sqlalchemy import select
from database.models import DailyEquitySnapshot
from database.repository import PositionRepository
from exchanges.binance.client import BinanceClient
from market.binance_public import ticker
from security.vault import CredentialVault
from core.config import settings

class PortfolioStateService:
    """Authoritative server-side portfolio state for the configured exchange account."""
    def __init__(self, exchange=None):
        self.exchange = exchange

    async def _asset_price(self, asset: str) -> float:
        asset = asset.upper()
        if asset == "USDT":
            return 1.0
        if asset == "USDC":
            return 1.0
        data = await self.exchange.get_price(f"{asset}USDT")
        return float(data["price"])

    async def equity_usdt(self, account: dict | None = None) -> float:
        account = account or await self.exchange.account()
        total = 0.0
        for b in account.get("balances", []):
            qty = float(b.get("free", 0)) + float(b.get("locked", 0))
            if qty <= 0:
                continue
            try:
                total += qty * await self._asset_price(b["asset"])
            except Exception:
                # Unknown/non-USDT asset is not silently valued at zero.
                # Refuse to produce an unsafe equity number.
                raise RuntimeError(f"Unable to value exchange asset {b['asset']} in USDT.")
        return total

    async def snapshot_and_risk_state(self, session, user_id: int) -> dict:
        if self.exchange is None:
            try:
                creds = await CredentialVault().get_provider_credentials(session, user_id, "binance")
                self.exchange = BinanceClient(creds.get("api_key"), creds.get("api_secret"), testnet=not settings.live_trading)
            except RuntimeError:
                if not settings.single_operator_mode:
                    raise
                self.exchange = BinanceClient(testnet=not settings.live_trading)
        account = await self.exchange.get_account()
        equity = await self.equity_usdt(account)
        usdt_free = 0.0
        for b in account.get("balances", []):
            if b.get("asset") == "USDT":
                usdt_free = float(b.get("free", 0))
                break

        today = datetime.now(timezone.utc).date().isoformat()
        result = await session.execute(select(DailyEquitySnapshot).where(
            DailyEquitySnapshot.user_id == user_id,
            DailyEquitySnapshot.date_key == today,
        ))
        snapshot = result.scalar_one_or_none()
        if snapshot is None:
            snapshot = DailyEquitySnapshot(
                user_id=user_id, date_key=today,
                starting_equity_usdt=equity,
            )
            session.add(snapshot)
            try:
                await session.commit()
            except Exception:
                await session.rollback()
                result = await session.execute(select(DailyEquitySnapshot).where(
                    DailyEquitySnapshot.user_id == user_id,
                    DailyEquitySnapshot.date_key == today,
                ))
                snapshot = result.scalar_one()

        daily_loss_pct = max(0.0, (snapshot.starting_equity_usdt - equity) / snapshot.starting_equity_usdt * 100) if snapshot.starting_equity_usdt > 0 else 100.0
        positions = await PositionRepository(session).open_positions(user_id)
        exposure = 0.0
        for p in positions:
            try:
                price = float((await self.exchange.get_price(p.symbol))["price"])
            except Exception:
                price = p.entry_price
            exposure += p.quantity * price

        return {
            "balance": usdt_free,
            "equity_usdt": equity,
            "exposure": exposure,
            "daily_loss_pct": daily_loss_pct,
            "open_positions": len(positions),
            "source": "server_exchange_account_and_database",
            "date_key": today,
        }
