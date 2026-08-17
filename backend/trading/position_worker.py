import asyncio
from trading.position_monitor import PositionMonitor
from market.binance_public import ticker

class PositionWorker:
    def __init__(self, repository):
        self.repository = repository
        self.monitor = PositionMonitor()

    async def tick(self, user_id: int):
        positions = await self.repository.open_positions(user_id)
        return await self._evaluate(positions)

    async def tick_all(self):
        # Used by the background worker, which monitors every open position
        # across every user — this is the "restart -> rediscover open
        # positions -> resume monitoring" path. Positions live in the
        # database (trading/position_worker persists nothing new here; it
        # reads whatever is already marked OPEN), so a process restart does
        # not lose track of them as long as the DB row exists.
        positions = await self.repository.all_open_positions()
        return await self._evaluate(positions)

    async def _evaluate(self, positions):
        results = []
        for p in positions:
            data = await ticker(p.symbol)
            current = float(data["lastPrice"])
            results.append({
                "position_id": p.id,
                "symbol": p.symbol,
                "current_price": current,
                "evaluation": self.monitor.evaluate(
                    p.side, p.entry_price, current,
                    p.stop_loss_price, p.take_profit_price
                )
            })
        return results
