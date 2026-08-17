'use client';
import { useEffect, useState } from 'react';
import { api } from '../lib/api';
import { Lang, t } from '../lib/i18n';
import { colors, Theme } from '../lib/theme';

type Item = { title: string; url: string; source: string; score: number; published_at: string | null };

export default function NewsPanel({ lang, theme, symbol }: { lang: Lang; theme: Theme; symbol: string }) {
  const c = colors(theme);
  const [items, setItems] = useState<Item[]>([]);
  const [sentiment, setSentiment] = useState<string>('');

  useEffect(() => {
    let cancelled = false;
    api.news(symbol).then(r => {
      if (cancelled) return;
      setItems(r.items || []);
      setSentiment(r.sentiment || '');
    }).catch(() => {});
    return () => { cancelled = true; };
  }, [symbol]);

  return (
    <div style={{ background: c.panel, border: `1px solid ${c.panelBorder}`, borderRadius: 12, padding: 16 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
        <h3 style={{ margin: 0, color: c.text, fontSize: 15 }}>{t(lang, 'news')} — {symbol}</h3>
        {sentiment && <span style={{ fontSize: 12, color: c.textMuted }}>{sentiment}</span>}
      </div>
      <div style={{ maxHeight: 220, overflowY: 'auto' }}>
        {items.slice(0, 8).map((it, i) => (
          <a key={i} href={it.url} target="_blank" rel="noreferrer"
            style={{ display: 'block', fontSize: 13, color: c.text, textDecoration: 'none', padding: '6px 0', borderTop: i ? `1px solid ${c.panelBorder}` : 'none' }}>
            {it.title}
            <span style={{ color: c.textMuted, fontSize: 11 }}> — {it.source.includes('coindesk') ? 'CoinDesk' : it.source.replace(/^https?:\/\//, '').split('/')[0]}</span>
          </a>
        ))}
        {items.length === 0 && <div style={{ color: c.textMuted, fontSize: 13 }}>—</div>}
      </div>
    </div>
  );
}
