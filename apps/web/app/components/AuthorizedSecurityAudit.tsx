'use client';

import { useEffect, useRef, useState } from 'react';
import { api } from '../lib/api';

type Finding = { id: string; severity: string; title: string; evidence: string; remediation: string };
type Report = { target: string; host: string; findings: Finding[]; summary: Record<string, number>; limitations: string[] };

const AUDIT_AUTH = 'i-authorize-this-security-test';
const DISCLOSURE_AUTH = 'i-authorize-this-disclosure';

export default function AuthorizedSecurityAudit() {
  const [listening, setListening] = useState(false);
  const [supported, setSupported] = useState(true);
  const [target, setTarget] = useState('');
  const [report, setReport] = useState<Report | null>(null);
  const [recipient, setRecipient] = useState('');
  const [auditAuthorization, setAuditAuthorization] = useState('');
  const [disclosureAuthorization, setDisclosureAuthorization] = useState('');
  const [status, setStatus] = useState('');
  const recognition = useRef<any>(null);
  const pendingTarget = useRef('');

  useEffect(() => {
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SR) { setSupported(false); return; }
    const rec = new SR();
    rec.continuous = false;
    rec.interimResults = false;
    rec.lang = 'en-IN';
    rec.onresult = async (event: any) => {
      const text = String(event.results?.[0]?.[0]?.transcript || '').trim();
      if (!text) return;
      const parsed = await api.voiceParse(text);
      if (parsed.intent === 'security_audit' && parsed.target) {
        pendingTarget.current = parsed.target;
        setTarget(parsed.target);
        setAuditAuthorization('');
        setStatus('Now say: I authorize this security test');
        speak('Now say: I authorize this security test');
      } else if (parsed.intent === 'security_audit_authorized' && (parsed.target || pendingTarget.current)) {
        const url = parsed.target || pendingTarget.current;
        await runScan(url, parsed.authorization || '');
        pendingTarget.current = '';
      } else {
        setStatus('Say: security audit followed by the full HTTPS URL.');
      }
    };
    rec.onend = () => setListening(false);
    rec.onerror = () => { setListening(false); setStatus('Voice recognition failed.'); };
    recognition.current = rec;
    return () => { try { rec.abort(); } catch {} };
  }, []);

  function speak(text: string) {
    if (!window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.lang = 'en-IN';
    window.speechSynthesis.speak(u);
  }

  function startVoice() {
    if (!recognition.current || listening) return;
    setStatus('Listening… say: security audit https://example.com');
    setListening(true);
    try { recognition.current.start(); } catch { setListening(false); }
  }

  async function runScan(url: string, authorization: string) {
    if (!url.trim()) { setStatus('Target URL is required.'); return; }
    if (authorization.trim().toLowerCase() !== AUDIT_AUTH) {
      setStatus('Explicit authorization phrase is required before scanning.');
      return;
    }
    setStatus('Running non-destructive authorized security audit…');
    try {
      const result = await api.securityAuditScan(url.trim(), authorization.trim());
      setReport(result);
      setDisclosureAuthorization('');
      const total = Object.values(result.summary || {}).reduce((a: number, b: number) => a + Number(b), 0);
      const message = `${total} findings returned. ${result.summary?.critical || 0} critical, ${result.summary?.high || 0} high, ${result.summary?.medium || 0} medium.`;
      setStatus(message);
      speak(message);
    } catch (error: any) {
      setStatus(error?.message || 'Audit failed.');
    }
  }

  async function disclose() {
    if (!report || !recipient.trim()) return;
    if (disclosureAuthorization.trim().toLowerCase() !== DISCLOSURE_AUTH) {
      setStatus('Explicit disclosure authorization phrase is required.');
      return;
    }
    setStatus('Sending responsible-disclosure report…');
    try {
      await api.securityAuditDisclose(recipient.trim(), report, disclosureAuthorization.trim());
      setStatus(`Disclosure sent to ${recipient.trim()}.`);
      setDisclosureAuthorization('');
      speak('Responsible disclosure sent.');
    } catch (error: any) {
      setStatus(error?.message || 'Disclosure failed.');
    }
  }

  return (
    <section aria-label="Authorized security auditor" style={{ marginTop: 10, padding: 12, borderRadius: 10, border: '1px solid rgba(99,232,255,.28)' }}>
      <div style={{ fontWeight: 800, fontSize: 12, marginBottom: 7 }}>🛡️ AUTHORIZED WEB SECURITY AUDITOR</div>
      {!supported && <div style={{ fontSize: 11 }}>Browser voice recognition is not supported.</div>}
      {supported && <button type="button" onClick={startVoice} disabled={listening} style={{ width: '100%', padding: 9, borderRadius: 8, border: 0, cursor: 'pointer' }}>{listening ? '🎙 Listening…' : '🎤 Start security audit by voice'}</button>}
      <input value={target} onChange={(e) => setTarget(e.target.value)} placeholder="Authorized target https://…" style={{ width: '100%', boxSizing: 'border-box', marginTop: 8, padding: 8, borderRadius: 7 }} />
      <input value={auditAuthorization} onChange={(e) => setAuditAuthorization(e.target.value)} placeholder="Type: I authorize this security test" autoComplete="off" style={{ width: '100%', boxSizing: 'border-box', marginTop: 6, padding: 8, borderRadius: 7 }} />
      <button type="button" onClick={() => runScan(target, auditAuthorization)} disabled={!target.trim() || !auditAuthorization.trim()} style={{ width: '100%', marginTop: 6, padding: 8, borderRadius: 7 }}>Run authorized scan</button>
      {status && <div style={{ marginTop: 7, fontSize: 11 }}>{status}</div>}
      {report && <div style={{ marginTop: 8, maxHeight: 230, overflowY: 'auto', fontSize: 11 }}>
        <div><b>{report.host}</b> — {report.findings.length} findings</div>
        {report.findings.map((f) => <div key={f.id} style={{ marginTop: 7, paddingBottom: 7, borderBottom: '1px solid rgba(255,255,255,.1)' }}><b>[{f.severity.toUpperCase()}] {f.title}</b><div>{f.evidence}</div><div>Fix: {f.remediation}</div></div>)}
        <input value={recipient} onChange={(e) => setRecipient(e.target.value)} placeholder="Disclosure recipient email" autoComplete="email" style={{ width: '100%', boxSizing: 'border-box', marginTop: 8, padding: 8, borderRadius: 7 }} />
        <input value={disclosureAuthorization} onChange={(e) => setDisclosureAuthorization(e.target.value)} placeholder="Type: I authorize this disclosure" autoComplete="off" style={{ width: '100%', boxSizing: 'border-box', marginTop: 6, padding: 8, borderRadius: 7 }} />
        <button type="button" onClick={disclose} disabled={!recipient.trim() || !disclosureAuthorization.trim()} style={{ width: '100%', marginTop: 6, padding: 8, borderRadius: 7 }}>Send responsible disclosure</button>
      </div>}
    </section>
  );
}
