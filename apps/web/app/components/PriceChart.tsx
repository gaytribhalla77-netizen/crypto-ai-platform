'use client';
import { useEffect, useState } from 'react';
import { api } from '../lib/api';
import { Lang, t } from '../lib/i18n';
import { colors, Theme } from '../lib/theme';

type Candle = { time: number; open: number; high: number; low: number; close: number; volume: number };

const INTERVALS = ['1m', '5m', '15m', '1h', '4h', '1d'];

export default function PriceChart({ lang, theme, symbol }: { lang: Lang; theme: Theme; symbol: string }) {
  const c = colors(theme);
  const [candles, setCandles] = useState<Candle[]>([]);
  const [interval, setInterval_] = useState('15m');
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setErr(null);
    try {
      const res = await api.klines(symbol, interval, 80);
      setCandles(res.candles);
    } catch (e: any) {
      setErr(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    const id = setInterval(load, 15000);
    return () => clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [symbol, interval]);

  const width = 720, height = 280, padding = 30;
  let svg = null;
  if (candles.length > 0) {
    const highs = candles.map(k => k.high);
    const lows = candles.map(k => k.low);
    const max = Math.max(...highs), min = Math.min(...lows);
    const range = max - min || 1;
    const cw = (width - padding * 2) / candles.length;

    const y = (price: number) => padding + (max - price) / range * (height - padding * 2);

    svg = (
      <svg width="100%" viewBox={`0 0 ${width} ${height}`} style={{ display: 'block' }}>
        {[0, 0.25, 0.5, 0.75, 1].map(f => {
          const price = max - range * f;
          const yy = padding + f * (height - padding * 2);
          return (
            <g key={f}>
              <line x1={padding} x2={width - padding} y1={yy} y2={yy} stroke={c.panelBorder} strokeWidth={1} />
              <text x={width - padding + 4} y={yy + 3} fontSize="9" fill={c.textMuted}>{price.toFixed(2)}</text>
            </g>
          );
        })}
        {candles.map((k, i) => {
          const x = padding + i * cw + cw / 2;
          const up = k.close >= k.open;
          const color = up ? c.green : c.red;
          const bodyTop = y(Math.max(k.open, k.close));
          const bodyBottom = y(Math.min(k.open, k.close));
          return (
            <g key={k.time}>
              <line x1={x} x2={x} y1={y(k.high)} y2={y(k.low)} stroke={color} strokeWidth={1} />
              <rect x={x - cw * 0.32} y={bodyTop} width={cw * 0.64}
                height={Math.max(1, bodyBottom - bodyTop)} fill={color} />
            </g>
          );
        })}
      </svg>
    );
  }

  return (
    <div style={{ background: c.panel, border: `1px solid ${c.panelBorder}`, borderRadius: 12, padding: 16 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
        <h3 style={{ margin: 0, color: c.text, fontSize: 15 }}>{t(lang, 'chart')} — {symbol}</h3>
        <div style={{ display: 'flex', gap: 4 }}>
          {INTERVALS.map(iv => (
            <button key={iv} onClick={() => setInterval_(iv)}
              style={{
                padding: '3px 8px', fontSize: 12, borderRadius: 6, cursor: 'pointer',
                border: `1px solid ${c.panelBorder}`,
                background: interval === iv ? c.accent : 'transparent',
                color: interval === iv ? '#fff' : c.textMuted,
              }}>{iv}</button>
          ))}
        </div>
      </div>
      {loading && candles.length === 0 && <div style={{ color: c.textMuted, fontSize: 13 }}>{t(lang, 'loading')}</div>}
      {err && <div style={{ color: c.red, fontSize: 13 }}>{err}</div>}
      {svg}
    </div>
  );
}
