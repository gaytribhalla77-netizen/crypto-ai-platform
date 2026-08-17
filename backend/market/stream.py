from __future__ import annotations
import asyncio, json
import websockets

class BinanceMarketStream:
    """Read-only market stream. It never submits orders."""
    def __init__(self, symbols=('btcusdt','ethusdt')):
        self.symbols=tuple(s.lower() for s in symbols); self.running=False
    async def run(self, on_event):
        streams='/'.join(f'{s}@bookTicker' for s in self.symbols)
        url=f'wss://stream.binance.com:9443/stream?streams={streams}'
        self.running=True
        delay=1
        while self.running:
            try:
                async with websockets.connect(url, ping_interval=20, ping_timeout=20, close_timeout=5) as ws:
                    delay=1
                    async for raw in ws:
                        if not self.running: break
                        data=json.loads(raw); await on_event(data)
            except asyncio.CancelledError: raise
            except Exception:
                await asyncio.sleep(min(delay,30)); delay*=2
    def stop(self): self.running=False
