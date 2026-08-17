'use client';

import { useEffect, useMemo, useState } from 'react';
import { API_BASE, getToken } from '../lib/api';

type Props = { symbol: string };

export default function RealtimeMonitor({ symbol }: Props) {
  const [state, setState] = useState<any>(null);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState('');

  const wsBase = useMemo(() => API_BASE.replace(/^http/, 'ws'), []);

  useEffect(() => {
    let ws: WebSocket | null = null;
    let stopped = false;
    const token = getToken();
    if (!token) { setError('Login required for live monitoring.'); return; }

    try {
      ws = new WebSocket(`${wsBase}/api/realtime/stream`);
      ws.onopen = () => {
        if (!stopped) {
          setConnected(true);
          ws?.send(JSON.stringify({ token }));
        }
      };
      ws.onmessage = (e) => {
        try {
          const msg = JSON.parse(e.data);
          if (msg.type === 'snapshot') setState(msg.payload);
          else setState((prev: any) => {
            const latest = { ...(prev?.latest || {}) };
            const current = { ...(latest[msg.symbol] || {}) };
            latest[msg.symbol] = { ...current, ...msg };
            return { ...(prev || {}), latest, recent_events: [...(prev?.recent_events || []).slice(-49), msg] };
          });
        } catch {}
      };
      ws.onerror = () => !stopped && setError('Live stream unavailable.');
      ws.onclose = () => !stopped && setConnected(false);
    } catch { setError('Live stream unavailable.'); }

    return () => { stopped = true; ws?.close(); };
  }, [wsBase, symbol]);

  const row = state?.latest?.[symbol];
  const news = row?.news;
  const impact = news?.market_impact;
  const tick = row?.mid;

  return (
    <div style={{ marginTop: 16, padding: 16, border: '1px solid rgba(255,255,255,.12)', borderRadius: 12 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, alignItems: 'center' }}>
        <div><b>REAL-TIME {symbol}</b><div style={{ fontSize: 11, opacity: .65 }}>Binance public market stream + news intelligence</div></div>
        <span style={{ fontSize: 11, fontWeight: 700 }}>{connected ? '● LIVE' : '○ OFFLINE'}</span>
      </div>
      {error && <div style={{ marginTop: 8, fontSize: 12 }}>{error}</div>}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 8, marginTop: 12 }}>
        <Metric label="MID" value={tick == null ? '—' : String(tick)} />
        <Metric label="SPREAD" value={row?.spread == null ? '—' : String(row.spread)} />
        <Metric label="NEWS" value={news?.sentiment || '—'} />
        <Metric label="IMPACT" value={impact?.severity || '—'} />
      </div>
      {impact?.severity && ['HIGH','CRITICAL'].includes(impact.severity) && (
        <div style={{ marginTop: 12, padding: 10, borderRadius: 8, border: '1px solid rgba(255,160,80,.4)' }}>
          <b>MARKET-MOVING NEWS: {impact.severity}</b>
          <div style={{ fontSize: 12, marginTop: 4 }}>{impact.direction || 'MIXED'} — {(impact.reasons || []).slice(0, 3).join(' · ') || 'Review current headlines before trading.'}</div>
        </div>
      )}
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return <div style={{ padding: 10, borderRadius: 8, background: 'rgba(255,255,255,.04)' }}><div style={{ fontSize: 10, opacity: .55 }}>{label}</div><b style={{ fontSize: 13 }}>{value}</b></div>;
}
