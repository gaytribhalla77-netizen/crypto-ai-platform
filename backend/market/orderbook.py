from __future__ import annotations
import httpx

BASE='https://testnet.binance.vision'
async def depth(symbol:str, limit:int=100)->dict:
    async with httpx.AsyncClient(timeout=5) as client:
        r=await client.get(f'{BASE}/api/v3/depth',params={'symbol':symbol.upper(),'limit':limit})
        r.raise_for_status(); data=r.json()
    bids=[(float(p),float(q)) for p,q in data.get('bids',[])]
    asks=[(float(p),float(q)) for p,q in data.get('asks',[])]
    bid=sum(p*q for p,q in bids); ask=sum(p*q for p,q in asks)
    total=bid+ask
    return {'symbol':symbol.upper(),'bid_notional':bid,'ask_notional':ask,'imbalance':(bid-ask)/total if total else 0.0,
            'best_bid':bids[0][0] if bids else None,'best_ask':asks[0][0] if asks else None}
