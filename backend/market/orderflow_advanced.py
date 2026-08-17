from __future__ import annotations
from statistics import mean

def analyze_sequence(snapshots:list[dict], depth:int=20):
    """Order-book sequence analytics. Spoofing is never asserted; only anomalies are flagged."""
    if not snapshots: return {'status':'no_data'}
    vals=[]
    for s in snapshots:
        bids=s.get('bids',[])[:depth]; asks=s.get('asks',[])[:depth]
        bv=sum(float(x[1]) for x in bids if len(x)>=2); av=sum(float(x[1]) for x in asks if len(x)>=2)
        total=bv+av; imb=(bv-av)/total if total else 0
        bb=float(bids[0][0]) if bids else 0; ba=float(asks[0][0]) if asks else 0
        spread=(ba-bb)/((ba+bb)/2) if bb and ba else 0
        vals.append({'imbalance':imb,'spread':spread,'bid_volume':bv,'ask_volume':av})
    imbs=[x['imbalance'] for x in vals]; spreads=[x['spread'] for x in vals]
    cancellation_like=sum(1 for a,b in zip(vals,vals[1:]) if abs(b['bid_volume']-a['bid_volume'])>max(1,a['bid_volume']*.35) or abs(b['ask_volume']-a['ask_volume'])>max(1,a['ask_volume']*.35))
    return {'samples':len(vals),'mean_imbalance':mean(imbs),'max_imbalance':max(imbs),'min_imbalance':min(imbs),'mean_spread':mean(spreads),'liquidity_vacuum':max(spreads)>max(1e-9,mean(spreads)*2),'rapid_depth_change_count':cancellation_like,'spoofing_like_anomaly':cancellation_like>=2,'regime':'BUY_PRESSURE' if mean(imbs)>.1 else 'SELL_PRESSURE' if mean(imbs)<-.1 else 'BALANCED'}
