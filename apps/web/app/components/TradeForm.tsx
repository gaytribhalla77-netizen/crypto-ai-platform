'use client';
import { useEffect, useState } from 'react';
import { api } from '../lib/api';
import { Lang, t } from '../lib/i18n';
import { colors, Theme } from '../lib/theme';

export default function TradeForm({
  lang, theme, symbol, loggedIn, onOrderPlaced,
}: { lang: Lang; theme: Theme; symbol: string; loggedIn: boolean; onOrderPlaced: () => void }) {
  const c = colors(theme);
  const [side, setSide] = useState<'BUY' | 'SELL'>('BUY');
  const [amount, setAmount] = useState(50);
  const [stopLossPct, setStopLossPct] = useState(5);
  const [takeProfitPct, setTakeProfitPct] = useState(5);
  const [price, setPrice] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    api.market(symbol).then(r => { if (!cancelled) setPrice(r.price); }).catch(() => {});
    return () => { cancelled = true; };
  }, [symbol]);

  async function submit() {
    setErr(null);
    setMsg(null);
    if (!loggedIn) { setErr(t(lang, 'loginRequired')); return; }
    if (!price) { setErr('Price not loaded yet.'); return; }
    setBusy(true);
    try {
      const quantity = Number((amount / price).toFixed(6));
      const res = await api.placeOrder({
        symbol, side, amount_usdt: amount, price, quantity,
        stop_loss_pct: stopLossPct, take_profit_pct: takeProfitPct,
        client_request_id: crypto.randomUUID(),
      });
      setMsg(`${res.status} — trade #${res.trade_id}${res.position_id ? `, position #${res.position_id}` : ''}`);
      onOrderPlaced();
    } catch (e: any) {
      setErr(e.message);
    } finally {
      setBusy(false);
    }
  }

  const inputStyle = {
    padding: 8, borderRadius: 8, border: `1px solid ${c.panelBorder}`,
    background: c.input, color: c.text, width: '100%', boxSizing: 'border-box' as const,
  };
  const labelStyle = { fontSize: 12, color: c.textMuted, marginBottom: 4, display: 'block' };

  return (
    <div style={{ background: c.panel, border: `1px solid ${c.panelBorder}`, borderRadius: 12, padding: 16 }}>
      <h3 style={{ margin: '0 0 12px', color: c.text, fontSize: 15 }}>{t(lang, 'trade')} — {symbol}</h3>

      <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
        {(['BUY', 'SELL'] as const).map(s => (
          <button key={s} onClick={() => setSide(s)}
            style={{
              flex: 1, padding: 10, borderRadius: 8, cursor: 'pointer', fontWeight: 700,
              border: `1px solid ${s === 'BUY' ? c.green : c.red}`,
              background: side === s ? (s === 'BUY' ? c.green : c.red) : 'transparent',
              color: side === s ? '#fff' : (s === 'BUY' ? c.green : c.red),
            }}>
            {t(lang, s === 'BUY' ? 'buy' : 'sell')}
          </button>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 10 }}>
        <div>
          <label style={labelStyle}>{t(lang, 'amount')}</label>
          <input type="number" min={1} value={amount} onChange={e => setAmount(Number(e.target.value))} style={inputStyle} />
        </div>
        <div>
          <label style={labelStyle}>{t(lang, 'price')}</label>
          <input value={price != null ? `$${price}` : '…'} readOnly style={inputStyle} />
        </div>
        <div>
          <label style={labelStyle} title={t(lang, 'stopLossHelp')}>{t(lang, 'stopLoss')}</label>
          <input type="number" min={0.5} max={50} step={0.5} value={stopLossPct}
            onChange={e => setStopLossPct(Number(e.target.value))} style={inputStyle} />
        </div>
        <div>
          <label style={labelStyle} title={t(lang, 'takeProfitHelp')}>{t(lang, 'takeProfit')}</label>
          <input type="number" min={0.5} step={0.5} value={takeProfitPct}
            onChange={e => setTakeProfitPct(Number(e.target.value))} style={inputStyle} />
        </div>
      </div>
      <div style={{ fontSize: 11, color: c.textMuted, marginBottom: 12 }}>
        {t(lang, 'stopLossHelp')} · {t(lang, 'takeProfitHelp')}
      </div>

      <button onClick={submit} disabled={busy}
        style={{
          width: '100%', padding: 12, borderRadius: 8, border: 'none', fontWeight: 700, cursor: 'pointer',
          background: side === 'BUY' ? c.green : c.red, color: '#fff',
        }}>
        {busy ? t(lang, 'loading') : t(lang, 'placeOrder')}
      </button>
      {msg && <div style={{ color: c.green, fontSize: 13, marginTop: 8 }}>{msg}</div>}
      {err && <div style={{ color: c.red, fontSize: 13, marginTop: 8 }}>{err}</div>}
    </div>
  );
}
