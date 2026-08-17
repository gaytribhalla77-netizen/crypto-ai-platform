'use client';
import { useEffect, useState } from 'react';
import { api } from '../lib/api';
import { Lang, t } from '../lib/i18n';
import { colors, Theme } from '../lib/theme';

export default function AIPrediction({ lang, theme, symbol }: { lang: Lang; theme: Theme; symbol: string }) {
  const c = colors(theme);
  const [pred, setPred] = useState<any>(null);
  const [acc, setAcc] = useState<any>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    setPred(null);
    api.mlAccuracy(symbol).then(setAcc).catch(() => setAcc(null));
  }, [symbol]);

  async function getPrediction() {
    setBusy(true);
    setErr(null);
    try {
      const res = await api.mlPredict(symbol);
      setPred(res);
      if (res.status === 'OK') {
        const a = await api.mlAccuracy(symbol);
        setAcc(a);
      }
    } catch (e: any) {
      setErr(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div style={{ background: c.panel, border: `1px solid ${c.panelBorder}`, borderRadius: 12, padding: 16 }}>
      <h3 style={{ margin: '0 0 10px', color: c.text, fontSize: 15 }}>{t(lang, 'aiPrediction')} — {symbol}</h3>

      <button onClick={getPrediction} disabled={busy}
        style={{ width: '100%', padding: 10, borderRadius: 8, border: 'none', background: c.accent, color: '#fff', cursor: 'pointer', fontWeight: 700, marginBottom: 10 }}>
        {busy ? t(lang, 'loading') : t(lang, 'getPrediction')}
      </button>

      {err && <div style={{ color: c.red, fontSize: 13 }}>{err}</div>}

      {pred?.status === 'NOT_TRAINED' && (
        <div style={{ color: c.textMuted, fontSize: 12 }}>
          {t(lang, 'notTrained')}<br />
          <code style={{ fontSize: 11 }}>{pred.message}</code>
        </div>
      )}
      {pred?.status && pred.status !== 'OK' && pred.status !== 'NOT_TRAINED' && (
        <div style={{ color: c.textMuted, fontSize: 12 }}>{pred.message}</div>
      )}

      {pred?.status === 'OK' && (
        <div style={{ marginBottom: 10 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
            <span style={{ fontSize: 22, fontWeight: 800, color: pred.direction === 'UP' ? c.green : c.red }}>
              {pred.direction === 'UP' ? '↑' : '↓'} {t(lang, pred.direction === 'UP' ? 'up' : 'down')}
            </span>
            <span style={{ fontSize: 13, color: c.textMuted }}>{pred.confidence}% confidence</span>
          </div>
          <div style={{ fontSize: 12, color: c.textMuted, marginTop: 4 }}>
            {t(lang, 'backtestAccuracy')}: {pred.model_backtest_accuracy_pct}%
          </div>
        </div>
      )}

      {acc && acc.sample_size > 0 && (
        <div style={{ borderTop: `1px solid ${c.panelBorder}`, paddingTop: 10 }}>
          <div style={{ fontSize: 12, color: c.textMuted, marginBottom: 4 }}>{t(lang, 'liveAccuracy')}</div>
          <div style={{ fontSize: 18, fontWeight: 700, color: acc.accuracy_pct >= 50 ? c.green : c.red }}>
            {acc.accuracy_pct}% <span style={{ fontSize: 12, color: c.textMuted, fontWeight: 400 }}>({acc.correct}/{acc.sample_size})</span>
          </div>
        </div>
      )}
      {acc && acc.sample_size === 0 && (
        <div style={{ fontSize: 12, color: c.textMuted, borderTop: `1px solid ${c.panelBorder}`, paddingTop: 10 }}>
          {t(lang, 'liveAccuracy')}: —
        </div>
      )}

      <div style={{ fontSize: 10, color: c.textMuted, marginTop: 10 }}>{t(lang, 'notFinancialAdvice')}</div>
    </div>
  );
}
