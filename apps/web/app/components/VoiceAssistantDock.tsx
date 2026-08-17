'use client';

import { useEffect, useState } from 'react';
import VoiceControl from './VoiceControl';
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
    <aside
      aria-label="Voice assistant"
      style={{
        position: 'fixed',
        right: 20,
        bottom: 20,
        width: 'min(360px, calc(100vw - 40px))',
        zIndex: 1000,
        boxShadow: '0 16px 48px rgba(0,0,0,.35)',
      }}
    >
      <VoiceControl
        lang={lang}
        theme={theme}
        loggedIn={loggedIn}
        onSymbolFound={() => undefined}
        onOrderPlaced={() => setLoggedIn(Boolean(getToken()))}
      />
      <div style={{ display: 'flex', gap: 6, marginTop: 6, justifyContent: 'flex-end' }}>
        <button type="button" onClick={() => setLang((v) => v === 'en' ? 'hi' : 'en')} style={{ padding: '4px 8px', borderRadius: 6 }}>
          {lang === 'en' ? 'हिंदी' : 'EN'}
        </button>
        <button type="button" onClick={() => setTheme((v) => v === 'dark' ? 'light' : 'dark')} style={{ padding: '4px 8px', borderRadius: 6 }}>
          {theme === 'dark' ? 'Light' : 'Dark'}
        </button>
      </div>
    </aside>
  );
}
