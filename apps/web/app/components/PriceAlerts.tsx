'use client';
import { useEffect, useRef, useState } from 'react';
import { api } from '../lib/api';
import { Lang, t } from '../lib/i18n';
import { colors, Theme } from '../lib/theme';

type Alert = { id: string; symbol: string; direction: 'above' | 'below'; target: number; fired: boolean };
const STORAGE_KEY = 'price_alerts_v1';

export default function PriceAlerts({ lang, theme, symbol }: { lang: Lang; theme: Theme; symbol: string }) {
  const c = colors(theme);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [target, setTarget] = useState<number | ''>('');
  const [direction, setDirection] = useState<'above' | 'below'>('above');
  const [permission, setPermission] = useState<NotificationPermission>('default');
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    const raw = typeof window !== 'undefined' ? window.localStorage.getItem(STORAGE_KEY) : null;
    if (raw) setAlerts(JSON.parse(raw));
    if (typeof Notification !== 'undefined') setPermission(Notification.permission);
  }, []);

  useEffect(() => {
    if (typeof window !== 'undefined') window.localStorage.setItem(STORAGE_KEY, JSON.stringify(alerts));
  }, [alerts]);

  useEffect(() => {
    async function poll() {
      const active = alerts.filter(a => !a.fired);
      if (active.length === 0) return;
      const symbols = Array.from(new Set(active.map(a => a.symbol)));
      const prices: Record<string, number> = {};
      for (const s of symbols) {
        try { prices[s] = (await api.market(s)).price; } catch { /* skip */ }
      }
      let changed = false;
      const next = alerts.map(a => {
        if (a.fired) return a;
        const price = prices[a.symbol];
        if (price == null) return a;
        const hit = a.direction === 'above' ? price >= a.target : price <= a.target;
        if (hit) {
          changed = true;
          if (typeof Notification !== 'undefined' && Notification.permission === 'granted') {
            new Notification(t(lang, 'alertFired'), { body: `${a.symbol} ${a.direction === 'above' ? '≥' : '≤'} $${a.target} (now $${price})` });
          }
          return { ...a, fired: true };
        }
        return a;
      });
      if (changed) setAlerts(next);
    }
    pollRef.current = setInterval(poll, 20000);
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [alerts, lang]);

  function requestPermission() {
    if (typeof Notification === 'undefined') return;
    Notification.requestPermission().then(setPermission);
  }

  function addAlert() {
    if (target === '' || isNaN(Number(target))) return;
    setAlerts([...alerts, { id: `${Date.now()}`, symbol, direction, target: Number(target), fired: false }]);
    setTarget('');
    if (permission !== 'granted') requestPermission();
  }

  function remove(id: string) {
    setAlerts(alerts.filter(a => a.id !== id));
  }

  const inputStyle = {
    padding: 8, borderRadius: 8, border: `1px solid ${c.panelBorder}`,
    background: c.input, color: c.text,
  };

  return (
    <div style={{ background: c.panel, border: `1px solid ${c.panelBorder}`, borderRadius: 12, padding: 16 }}>
      <h3 style={{ margin: '0 0 10px', color: c.text, fontSize: 15 }}>{t(lang, 'alerts')}</h3>
      <div style={{ display: 'flex', gap: 8, marginBottom: 10, flexWrap: 'wrap' }}>
        <select value={direction} onChange={e => setDirection(e.target.value as any)} style={inputStyle}>
          <option value="above">{t(lang, 'above')}</option>
          <option value="below">{t(lang, 'below')}</option>
        </select>
        <input type="number" placeholder={t(lang, 'targetPrice')} value={target}
          onChange={e => setTarget(e.target.value === '' ? '' : Number(e.target.value))} style={{ ...inputStyle, width: 120 }} />
        <button onClick={addAlert}
          style={{ padding: '8px 14px', borderRadius: 8, border: 'none', background: c.accent, color: '#fff', cursor: 'pointer' }}>
          {t(lang, 'setAlert')}
        </button>
      </div>
      {permission !== 'granted' && (
        <div style={{ fontSize: 12, color: c.textMuted, marginBottom: 8 }}>
          <button onClick={requestPermission}
            style={{ background: 'none', border: `1px solid ${c.panelBorder}`, borderRadius: 6, padding: '2px 8px', color: c.textMuted, cursor: 'pointer' }}>
            Enable browser notifications
          </button>
        </div>
      )}
      {alerts.length === 0 && <div style={{ color: c.textMuted, fontSize: 13 }}>{t(lang, 'noAlerts')}</div>}
      {alerts.map(a => (
        <div key={a.id} style={{
          display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: 13,
          padding: '6px 0', borderTop: `1px solid ${c.panelBorder}`, color: a.fired ? c.textMuted : c.text,
        }}>
          <span>{a.symbol} {a.direction === 'above' ? '≥' : '≤'} ${a.target} {a.fired ? `(${t(lang, 'alertFired')})` : ''}</span>
          <button onClick={() => remove(a.id)}
            style={{ background: 'none', border: 'none', color: c.red, cursor: 'pointer', fontSize: 12 }}>
            {t(lang, 'remove')}
          </button>
        </div>
      ))}
    </div>
  );
}
