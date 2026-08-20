'use client';

import { useEffect, useState } from 'react';
import VoiceControl from './VoiceControl';
import AuthorizedSecurityAudit from './AuthorizedSecurityAudit';
import { getToken } from '../lib/api';
import type { Lang } from '../lib/i18n';
import type { Theme } from '../lib/theme';

export default function VoiceAssistantDock() {
  const [lang, setLang] = useState<Lang>('en');
  const [theme, setTheme] = useState<Theme>('dark');
  const [loggedIn, setLoggedIn] = useState(false);

  useEffect(() => {
    setLoggedIn(Boolean(getToken()));
    const storedLang = window.localStorage.getItem('language');
    const storedTheme = window.localStorage.getItem('theme');
    if (storedLang === 'en' || storedLang === 'hi') setLang(storedLang);
    if (storedTheme === 'dark' || storedTheme === 'light') setTheme(storedTheme);
  }, []);

  return (
    <aside aria-label="IQ200 Voice Assistant" style={{ position: 'fixed', right: 'max(12px, env(safe-area-inset-right))', bottom: 'max(12px, env(safe-area-inset-bottom))', width: 'min(360px, calc(100vw - 24px))', maxHeight: 'calc(100vh - 24px)', overflowY: 'auto', zIndex: 10000, pointerEvents: 'auto', boxShadow: '0 16px 48px rgba(0,0,0,.45)', borderRadius: 14 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8, padding: '7px 10px', background: 'rgba(5,9,18,.96)', color: '#eef5ff', border: '1px solid rgba(99,232,255,.28)', borderBottom: 0, borderRadius: '14px 14px 0 0', fontSize: 11, fontWeight: 800, letterSpacing: '.08em' }}>
        <span>🎤 IQ200 VOICE ASSISTANT</span><span style={{ opacity: .65 }}>{lang === 'hi' ? 'हिंदी' : 'EN'}</span>
      </div>
      <VoiceControl lang={lang} theme={theme} loggedIn={loggedIn} onSymbolFound={() => undefined} onOrderPlaced={() => setLoggedIn(Boolean(getToken()))} />
      <AuthorizedSecurityAudit />
      <div style={{ display: 'flex', gap: 6, marginTop: 0, padding: '6px 8px 8px', justifyContent: 'flex-end', background: 'rgba(5,9,18,.96)', border: '1px solid rgba(99,232,255,.28)', borderTop: 0, borderRadius: '0 0 14px 14px' }}>
        <button type="button" onClick={() => setLang((v) => v === 'en' ? 'hi' : 'en')} style={{ padding: '5px 9px', borderRadius: 7 }}>{lang === 'en' ? 'हिंदी' : 'EN'}</button>
        <button type="button" onClick={() => setTheme((v) => v === 'dark' ? 'light' : 'dark')} style={{ padding: '5px 9px', borderRadius: 7 }}>{theme === 'dark' ? 'Light' : 'Dark'}</button>
      </div>
    </aside>
  );
}
