'use client';
import { useEffect, useState } from 'react';
import { api } from '../lib/api';
import { Lang, t } from '../lib/i18n';
import { colors, Theme } from '../lib/theme';

type Row = {
  symbol: string; price: number | null; change_24h_pct: number | null;
  sentiment: string; sentiment_score: number; news_count: number; error?: string;
};

export default function Watchlist({
  lang, theme, selected, onSelect,
}: { lang: Lang; theme: Theme; selected: string; onSelect: (s: string) => void }) {
  const c = colors(theme);
  const [rows, setRows] = useState<Row[]>([]);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    try {
      const res = await api.watchlist();
      setRows(res.watchlist);
    } catch {
      // public endpoint; swallow transient errors, keep last-known rows
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    const id = setInterval(load, 30000);
    return () => clearInterval(id);
  }, []);

  function sentimentColor(s: string) {
    if (s === 'BULLISH') return c.green;
    if (s === 'BEARISH') return c.red;
    return c.textMuted;
  }

  return (
    <div style={{ background: c.panel, border: `1px solid ${c.panelBorder}`, borderRadius: 12, padding: 16 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
        <h3 style={{ margin: 0, color: c.text, fontSize: 15 }}>{t(lang, 'watchlist')}</h3>
        {loading && <span style={{ color: c.textMuted, fontSize: 12 }}>{t(lang, 'loading')}</span>}
      </div>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
        <thead>
          <tr style={{ color: c.textMuted, textAlign: 'left' }}>
            <th style={{ padding: '4px 6px' }}>{t(lang, 'symbol')}</th>
            <th style={{ padding: '4px 6px' }}>{t(lang, 'price')}</th>
            <th style={{ padding: '4px 6px' }}>{t(lang, 'change24h')}</th>
            <th style={{ padding: '4px 6px' }}>{t(lang, 'sentiment')}</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(r => (
            <tr key={r.symbol}
              onClick={() => onSelect(r.symbol)}
              style={{
                cursor: 'pointer', color: c.text,
                background: selected === r.symbol ? c.input : 'transparent',
                borderRadius: 8,
              }}>
              <td style={{ padding: '6px', fontWeight: 600 }}>{r.symbol.replace('USDT', '')}</td>
              <td style={{ padding: '6px' }}>{r.price != null ? `$${r.price.toLocaleString()}` : '—'}</td>
              <td style={{ padding: '6px', color: (r.change_24h_pct ?? 0) >= 0 ? c.green : c.red }}>
                {r.change_24h_pct != null ? `${r.change_24h_pct.toFixed(2)}%` : '—'}
              </td>
              <td style={{ padding: '6px', color: sentimentColor(r.sentiment) }}>
                {r.sentiment} {r.news_count ? `(${r.news_count})` : ''}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
