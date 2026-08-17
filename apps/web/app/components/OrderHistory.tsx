'use client';
import { useEffect, useState } from 'react';
import { api } from '../lib/api';
import { Lang, t } from '../lib/i18n';
import { colors, Theme } from '../lib/theme';

type Trade = {
  id: number; symbol: string; side: string; amount_usdt: number;
  status: string; created_at: string | null;
};

export default function OrderHistory({
  lang, theme, loggedIn, refreshKey,
}: { lang: Lang; theme: Theme; loggedIn: boolean; refreshKey: number }) {
  const c = colors(theme);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    if (!loggedIn) return;
    api.history(50).then(r => setTrades(r.trades)).catch(e => setErr(e.message));
  }, [loggedIn, refreshKey]);

  function statusColor(s: string) {
    if (['FILLED', 'ACKNOWLEDGED'].includes(s)) return c.green;
    if (['REJECTED', 'CANCELLED', 'EXPIRED', 'FAILED'].includes(s)) return c.red;
    return c.textMuted;
  }

  return (
    <div style={{ background: c.panel, border: `1px solid ${c.panelBorder}`, borderRadius: 12, padding: 16 }}>
      <h3 style={{ margin: '0 0 10px', color: c.text, fontSize: 15 }}>{t(lang, 'history')}</h3>
      {!loggedIn && <div style={{ color: c.textMuted, fontSize: 13 }}>{t(lang, 'loginRequired')}</div>}
      {err && <div style={{ color: c.red, fontSize: 13 }}>{err}</div>}
      {loggedIn && (
        <div style={{ maxHeight: 320, overflowY: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <thead>
              <tr style={{ color: c.textMuted, textAlign: 'left', position: 'sticky', top: 0, background: c.panel }}>
                <th style={{ padding: '4px 6px' }}>{t(lang, 'date')}</th>
                <th style={{ padding: '4px 6px' }}>{t(lang, 'symbol')}</th>
                <th style={{ padding: '4px 6px' }}>{t(lang, 'side')}</th>
                <th style={{ padding: '4px 6px' }}>{t(lang, 'amount')}</th>
                <th style={{ padding: '4px 6px' }}>{t(lang, 'status')}</th>
              </tr>
            </thead>
            <tbody>
              {trades.map(tr => (
                <tr key={tr.id} style={{ color: c.text }}>
                  <td style={{ padding: '6px' }}>{tr.created_at ? new Date(tr.created_at).toLocaleString() : '—'}</td>
                  <td style={{ padding: '6px', fontWeight: 600 }}>{tr.symbol}</td>
                  <td style={{ padding: '6px', color: tr.side === 'BUY' ? c.green : c.red }}>{tr.side}</td>
                  <td style={{ padding: '6px' }}>${tr.amount_usdt}</td>
                  <td style={{ padding: '6px', color: statusColor(tr.status) }}>{tr.status}</td>
                </tr>
              ))}
              {trades.length === 0 && (
                <tr><td colSpan={5} style={{ padding: 10, color: c.textMuted }}>—</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
