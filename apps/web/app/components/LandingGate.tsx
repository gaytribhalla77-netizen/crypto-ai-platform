'use client';

import { useEffect, useState } from 'react';

export default function LandingGate() {
  const [open, setOpen] = useState(true);

  useEffect(() => {
    setOpen(window.sessionStorage.getItem('iq200_entered_dashboard') !== '1');
  }, []);

  if (!open) return null;

  const enter = () => {
    window.sessionStorage.setItem('iq200_entered_dashboard', '1');
    setOpen(false);
  };

  return (
    <section style={{ position: 'fixed', inset: 0, zIndex: 2000, overflowY: 'auto', background: 'radial-gradient(circle at 50% 0%, rgba(80,110,255,.22), transparent 42%), #05070d', color: '#f5f7ff' }}>
      <div style={{ maxWidth: 1180, margin: '0 auto', padding: '28px 24px 70px' }}>
        <nav style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 20 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{ width: 42, height: 42, borderRadius: 13, display: 'grid', placeItems: 'center', background: 'linear-gradient(135deg,#7c5cff,#19d3ff)', fontWeight: 900 }}>IQ</div>
            <div><b style={{ fontSize: 18 }}>IQ200</b><div style={{ fontSize: 10, opacity: .55, letterSpacing: 1.5 }}>ADAPTIVE MARKET INTELLIGENCE</div></div>
          </div>
          <button onClick={enter} style={{ border: '1px solid rgba(255,255,255,.14)', background: 'rgba(255,255,255,.06)', color: '#fff', borderRadius: 10, padding: '10px 16px', cursor: 'pointer' }}>Open Dashboard</button>
        </nav>

        <div style={{ textAlign: 'center', padding: '92px 0 70px' }}>
          <div style={{ display: 'inline-block', padding: '7px 12px', borderRadius: 999, border: '1px solid rgba(120,150,255,.3)', background: 'rgba(100,120,255,.08)', fontSize: 12, letterSpacing: 1.2 }}>AI-POWERED CRYPTO TRADING</div>
          <h1 style={{ fontSize: 'clamp(42px, 7vw, 82px)', lineHeight: .98, margin: '22px auto', maxWidth: 900, letterSpacing: -3 }}>Trade smarter with <span style={{ background: 'linear-gradient(90deg,#8b6cff,#28d8ff)', WebkitBackgroundClip: 'text', color: 'transparent' }}>AI intelligence.</span></h1>
          <p style={{ maxWidth: 680, margin: '0 auto', color: 'rgba(245,247,255,.68)', fontSize: 18, lineHeight: 1.65 }}>A professional crypto command center with real market evidence, risk-gated execution, multi-agent intelligence and a voice trading assistant.</p>
          <div style={{ display: 'flex', justifyContent: 'center', gap: 12, flexWrap: 'wrap', marginTop: 30 }}>
            <button onClick={enter} style={{ border: 0, background: 'linear-gradient(90deg,#735cff,#16c8ff)', color: '#fff', fontWeight: 800, borderRadius: 12, padding: '14px 24px', cursor: 'pointer', fontSize: 15 }}>Launch Trading Dashboard →</button>
            <button onClick={() => document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' })} style={{ border: '1px solid rgba(255,255,255,.14)', background: 'rgba(255,255,255,.05)', color: '#fff', borderRadius: 12, padding: '14px 24px', cursor: 'pointer', fontSize: 15 }}>Explore Features</button>
          </div>
        </div>

        <div id="features" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(220px,1fr))', gap: 16 }}>
          {[
            ['🎤', 'Voice Assistant', 'Speak naturally to query markets, news, portfolio and supported trading actions.'],
            ['🧠', 'AI Intelligence', 'Multi-agent market reasoning designed around evidence instead of invented signals.'],
            ['🛡️', 'Risk First', 'Fail-closed controls and confirmation gates protect the execution path.'],
            ['📊', 'Live Market Data', 'Track prices, market evidence, providers and system health from one cockpit.'],
          ].map(([icon, title, text]) => (
            <article key={title} style={{ padding: 22, borderRadius: 18, border: '1px solid rgba(255,255,255,.1)', background: 'rgba(255,255,255,.045)', backdropFilter: 'blur(16px)' }}>
              <div style={{ fontSize: 27 }}>{icon}</div><h3 style={{ margin: '14px 0 8px' }}>{title}</h3><p style={{ margin: 0, color: 'rgba(245,247,255,.62)', lineHeight: 1.55, fontSize: 14 }}>{text}</p>
            </article>
          ))}
        </div>

        <div style={{ marginTop: 18, padding: 26, borderRadius: 20, border: '1px solid rgba(255,255,255,.1)', background: 'linear-gradient(135deg,rgba(110,90,255,.12),rgba(20,200,255,.05))', display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(180px,1fr))', gap: 20 }}>
          {[['REAL-TIME','Market telemetry'],['AI','Decision intelligence'],['FAIL-CLOSED','Risk authority'],['VOICE','Hands-free control']].map(([a,b]) => <div key={a}><b style={{ display: 'block', fontSize: 20 }}>{a}</b><span style={{ color: 'rgba(245,247,255,.55)', fontSize: 12 }}>{b}</span></div>)}
        </div>
      </div>
    </section>
  );
}
