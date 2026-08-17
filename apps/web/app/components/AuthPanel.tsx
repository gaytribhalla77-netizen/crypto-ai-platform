'use client';
import { useState } from 'react';
import { api, setToken } from '../lib/api';
import { Lang, t } from '../lib/i18n';
import { colors, Theme } from '../lib/theme';

export default function AuthPanel({
  lang, theme, onAuth,
}: { lang: Lang; theme: Theme; onAuth: () => void }) {
  const c = colors(theme);
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    setBusy(true);
    try {
      const fn = mode === 'login' ? api.login : api.register;
      const res = await fn(email, password);
      setToken(res.access_token);
      onAuth();
    } catch (e: any) {
      setErr(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
      <input placeholder={t(lang, 'email')} value={email} onChange={e => setEmail(e.target.value)}
        style={{ padding: 8, borderRadius: 8, border: `1px solid ${c.panelBorder}`, background: c.input, color: c.text }} />
      <input placeholder={t(lang, 'password')} type="password" value={password} onChange={e => setPassword(e.target.value)}
        style={{ padding: 8, borderRadius: 8, border: `1px solid ${c.panelBorder}`, background: c.input, color: c.text }} />
      <button type="submit" disabled={busy}
        style={{ padding: '8px 14px', borderRadius: 8, border: 'none', background: c.accent, color: '#fff', cursor: 'pointer' }}>
        {t(lang, mode)}
      </button>
      <button type="button" onClick={() => setMode(mode === 'login' ? 'register' : 'login')}
        style={{ padding: '8px 10px', borderRadius: 8, border: `1px solid ${c.panelBorder}`, background: 'transparent', color: c.textMuted, cursor: 'pointer' }}>
        {mode === 'login' ? t(lang, 'register') : t(lang, 'login')}
      </button>
      {err && <span style={{ color: c.red, fontSize: 13 }}>{err}</span>}
    </form>
  );
}
