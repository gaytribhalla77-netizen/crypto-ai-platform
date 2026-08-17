'use client';
import { useEffect, useState } from 'react';
import { api } from '../lib/api';
import { Lang, t } from '../lib/i18n';
import { colors, Theme } from '../lib/theme';

type Portfolio = {
  open_position_count: number; invested_usdt: number; current_value_usdt: number;
  unrealized_pnl_usdt: number; unrealized_pnl_pct: number;
  positions: { symbol: string; quantity: number; entry_price: number; current_price: number; pnl_usdt: number; pnl_pct: number }[];
};

export default function PortfolioSummary({
  lang, theme, loggedIn, refreshKey,
}: { lang: Lang; theme: Theme; loggedIn: boolean; refreshKey: number }) {
  const c = colors(theme);
  const [p, setP] = useState<Portfolio | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    if (!loggedIn) return;
    function load() {
      api.portfolio().then(setP).catch(e => setErr(e.message));
    }
    load();
    const id = setInterval(load, 20000);
    return () => clearInterval(id);
  }, [loggedIn, refreshKey]);

  const stat = (label: string, value: string, color?: string) => (
    <div>
      <div style={{ fontSize: 11, color: c.textMuted }}>{label}</div>
      <div style={{ fontSize: 18, fontWeight: 700, color: color || c.text }}>{value}</div>
    </div>
  );

  return (
    <div style={{ background: c.panel, border: `1px solid ${c.panelBorder}`, borderRadius: 12, padding: 16 }}>
      <h3 style={{ margin: '0 0 10px', color: c.text, fontSize: 15 }}>{t(lang, 'portfolio')}</h3>
      {!loggedIn && <div style={{ color: c.textMuted, fontSize: 13 }}>{t(lang, 'loginRequired')}</div>}
      {err && <div style={{ color: c.red, fontSize: 13 }}>{err}</div>}
      {p && (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginBottom: 14 }}>
            {stat(t(lang, 'invested'), `$${p.invested_usdt.toLocaleString()}`)}
            {stat(t(lang, 'currentValue'), `$${p.current_value_usdt.toLocaleString()}`)}
            {stat(t(lang, 'unrealizedPnl'), `${p.unrealized_pnl_usdt >= 0 ? '+' : ''}$${p.unrealized_pnl_usdt.toLocaleString()} (${p.unrealized_pnl_pct}%)`,
              p.unrealized_pnl_usdt >= 0 ? c.green : c.red)}
            {stat(t(lang, 'openPositions'), String(p.open_position_count))}
          </div>
          {p.positions.length === 0 && <div style={{ color: c.textMuted, fontSize: 13 }}>{t(lang, 'noPositions')}</div>}
          {p.positions.map((row, i) => (
            <div key={i} style={{
              display: 'flex', justifyContent: 'space-between', fontSize: 13,
              padding: '6px 0', borderTop: `1px solid ${c.panelBorder}`, color: c.text,
            }}>
              <span style={{ fontWeight: 600 }}>{row.symbol}</span>
              <span style={{ color: c.textMuted }}>{row.quantity} @ ${row.entry_price}</span>
              <span style={{ color: row.pnl_usdt >= 0 ? c.green : c.red }}>
                {row.pnl_usdt >= 0 ? '+' : ''}${row.pnl_usdt} ({row.pnl_pct}%)
              </span>
            </div>
          ))}
        </>
      )}
    </div>
  );
}
