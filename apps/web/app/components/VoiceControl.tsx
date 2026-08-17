'use client';
import { useEffect, useRef, useState } from 'react';
import { api, API_BASE } from '../lib/api';
import { Lang, t } from '../lib/i18n';
import { colors, Theme } from '../lib/theme';

type PendingTrade = { side: 'BUY' | 'SELL'; symbol: string; amount_usdt: number };

export default function VoiceControl({
  lang, theme, loggedIn, onSymbolFound, onOrderPlaced,
}: {
  lang: Lang; theme: Theme; loggedIn: boolean;
  onSymbolFound?: (symbol: string) => void; onOrderPlaced?: () => void;
}) {
  const c = colors(theme);
  const [supported, setSupported] = useState(true);
  const [listening, setListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [reply, setReply] = useState('');
  const [pending, setPending] = useState<PendingTrade | null>(null);
  const [busy, setBusy] = useState(false);
  const [totp, setTotp] = useState('');
  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SR) { setSupported(false); return; }
    const rec = new SR();
    // en-IN (not hi-IN) transcribes code-switched Hindi/English speech into
    // Latin script most reliably in Chrome, which is what the backend's
    // keyword parser expects (it matches "kharido", not "खरीदो").
    rec.lang = 'en-IN';
    rec.continuous = false;
    rec.interimResults = false;
    rec.onresult = (e: any) => {
      const text = e.results[0][0].transcript;
      setTranscript(text);
      handleCommand(text);
    };
    rec.onend = () => setListening(false);
    rec.onerror = () => setListening(false);
    recognitionRef.current = rec;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function speak(text: string) {
    if (typeof window === 'undefined' || !window.speechSynthesis) return;
    const u = new SpeechSynthesisUtterance(text);
    u.lang = lang === 'hi' ? 'hi-IN' : 'en-IN';
    window.speechSynthesis.speak(u);
  }

  function startListening() {
    if (!recognitionRef.current) return;
    setReply('');
    setListening(true);
    try { recognitionRef.current.start(); } catch { setListening(false); }
  }

  async function handleCommand(text: string) {
    setBusy(true);
    try {
      const intent = await api.voiceParse(text);

      if (pending) {
        if (intent.intent === 'confirm') { await executeTrade(); return; }
        if (intent.intent === 'cancel') { setPending(null); say(lang === 'hi' ? 'Cancel kar diya.' : 'Cancelled.'); return; }
      }

      switch (intent.intent) {
        case 'price': {
          if (!intent.symbol) { say(t(lang, 'voicePlaceholder')); break; }
          const m = await api.market(intent.symbol);
          onSymbolFound?.(intent.symbol);
          say(`${intent.symbol.replace('USDT', '')} $${m.price}`);
          break;
        }
        case 'watchlist': {
          const w = await api.watchlist();
          const top = w.watchlist.slice(0, 5).map((r: any) => `${r.symbol.replace('USDT', '')} $${r.price}`).join(', ');
          say(top || '—');
          break;
        }
        case 'portfolio': {
          if (!loggedIn) { say(t(lang, 'loginRequired')); break; }
          const p = await api.portfolio();
          say(`${lang === 'hi' ? 'Invest kiya' : 'Invested'} $${p.invested_usdt}, ${lang === 'hi' ? 'profit loss' : 'P and L'} $${p.unrealized_pnl_usdt}`);
          break;
        }
        case 'positions': {
          if (!loggedIn) { say(t(lang, 'loginRequired')); break; }
          const pos = await api.positions();
          say(pos.count === 0 ? t(lang, 'noPositions') : `${pos.count} ${lang === 'hi' ? 'open positions hain' : 'open positions'}`);
          break;
        }
        case 'history': {
          if (!loggedIn) { say(t(lang, 'loginRequired')); break; }
          const h = await api.history(5);
          say(h.count === 0 ? '—' : h.trades.map((tr: any) => `${tr.side} ${tr.symbol}`).join(', '));
          break;
        }
        case 'news': {
          if (!intent.symbol) { say(t(lang, 'voicePlaceholder')); break; }
          const n = await api.news(intent.symbol);
          say(`${intent.symbol.replace('USDT', '')}: ${n.sentiment}, ${n.count} ${lang === 'hi' ? 'headlines' : 'headlines'}`);
          break;
        }
        case 'info': {
          if (!intent.symbol) { say(t(lang, 'voicePlaceholder')); break; }
          const full = await api.intel(intent.symbol);
          onSymbolFound?.(intent.symbol);
          const m = full.market;
          const parts = [];
          if (m?.price) parts.push(`$${m.price}, ${m.trend}`);
          if (full.news?.sentiment) parts.push(`${lang === 'hi' ? 'news' : 'news'} ${full.news.sentiment}`);
          if (full.ai_prediction?.status === 'OK') {
            parts.push(`AI ${full.ai_prediction.direction} (${full.ai_prediction.confidence}%)`);
          } else {
            parts.push(lang === 'hi' ? 'AI model trained nahi hai' : 'AI model not trained yet');
          }
          if (full.ai_track_record?.sample_size > 0) {
            parts.push(`${lang === 'hi' ? 'track record' : 'track record'} ${full.ai_track_record.accuracy_pct}%`);
          }
          say(`${intent.symbol.replace('USDT', '')}: ${parts.join('. ')}`);
          break;
        }
        case 'trade': {
          if (intent.missing?.length) { say(intent.message); break; }
          setPending({ side: intent.side, symbol: intent.symbol, amount_usdt: intent.amount_usdt });
          say(intent.message);
          break;
        }
        default:
          say(intent.message || t(lang, 'voiceNotSupported'));
      }
    } catch (e: any) {
      say(e.message || t(lang, 'error'));
    } finally {
      setBusy(false);
    }
  }

  function say(text: string) {
    setReply(text);
    speak(text);
  }

  async function executeTrade() {
    if (!pending) return;
    if (!loggedIn) { say(t(lang, 'loginRequired')); setPending(null); return; }
    setBusy(true);
    try {
      const m = await api.market(pending.symbol);
      const quantity = Number((pending.amount_usdt / m.price).toFixed(6));
      const base = API_BASE.replace(/\/$/, '');
      const h = await fetch(`${base}/health`, { cache: 'no-store' }).then(r => r.json());
      const live = Boolean(h?.live_trading);
      if (live && !totp) { say(lang === 'hi' ? 'Live trade ke liye 6-digit authenticator code enter karein.' : 'Enter your 6-digit authenticator code for the live trade.'); return; }
      const res = await api.placeOrder({
        symbol: pending.symbol, side: pending.side, amount_usdt: pending.amount_usdt,
        price: m.price, quantity,
        stop_loss_pct: 5, take_profit_pct: 5,
        client_request_id: crypto.randomUUID(),
        live, totp_code: live ? totp : undefined,
      });
      say(`${res.status}. ${lang === 'hi' ? 'Order number' : 'Order'} ${res.trade_id}.`);
      onOrderPlaced?.();
    } catch (e: any) {
      say(e.message);
    } finally {
      setTotp('');
      setPending(null);
      setBusy(false);
    }
  }

  function cancelTrade() {
    setPending(null);
    say(lang === 'hi' ? 'Cancel kar diya.' : 'Cancelled.');
  }

  return (
    <div style={{ background: c.panel, border: `1px solid ${c.panelBorder}`, borderRadius: 12, padding: 16 }}>
      <h3 style={{ margin: '0 0 10px', color: c.text, fontSize: 15 }}>{t(lang, 'voice')}</h3>
      {!supported && <div style={{ color: c.red, fontSize: 13 }}>{t(lang, 'voiceNotSupported')}</div>}
      {supported && (
        <>
          <button onClick={startListening} disabled={listening || busy}
            style={{
              width: '100%', padding: 14, borderRadius: 10, border: 'none', cursor: 'pointer', fontWeight: 700,
              background: listening ? c.red : c.accent, color: '#fff', marginBottom: 10,
            }}>
            {listening ? `🎙 ${t(lang, 'listening')}` : `🎤 ${t(lang, 'tapToSpeak')}`}
          </button>
          {transcript && <div style={{ fontSize: 12, color: c.textMuted, marginBottom: 6 }}>“{transcript}”</div>}
          {reply && <div style={{ fontSize: 13, color: c.text, marginBottom: 10 }}>{reply}</div>}

          {pending && (
            <div style={{ border: `1px solid ${c.accent}`, borderRadius: 8, padding: 10, marginBottom: 10 }}>
              <div style={{ fontSize: 13, color: c.text, marginBottom: 8 }}>
                {t(lang, 'confirmTrade')} <b>{pending.side}</b> ${pending.amount_usdt} {pending.symbol.replace('USDT', '')}
              </div>
              <div style={{ fontSize: 11, color: c.textMuted, marginBottom: 8 }}>{t(lang, 'sayConfirm')}</div>
              <input value={totp} onChange={e => setTotp(e.target.value.replace(/\D/g, '').slice(0, 6))} placeholder="Authenticator 6-digit code (live only)" inputMode="numeric" maxLength={6} style={{ width: '100%', boxSizing: 'border-box', padding: 8, borderRadius: 8, marginBottom: 8, border: `1px solid ${c.panelBorder}`, background: 'transparent', color: c.text }} />
              <div style={{ display: 'flex', gap: 8 }}>
                <button onClick={executeTrade} disabled={busy}
                  style={{ flex: 1, padding: 8, borderRadius: 8, border: 'none', background: c.green, color: '#fff', cursor: 'pointer', fontWeight: 700 }}>
                  {t(lang, 'yes')}
                </button>
                <button onClick={cancelTrade}
                  style={{ flex: 1, padding: 8, borderRadius: 8, border: `1px solid ${c.panelBorder}`, background: 'transparent', color: c.text, cursor: 'pointer' }}>
                  {t(lang, 'no')}
                </button>
              </div>
            </div>
          )}
          <div style={{ fontSize: 11, color: c.textMuted }}>{t(lang, 'voicePlaceholder')}</div>
        </>
      )}
    </div>
  );
}
