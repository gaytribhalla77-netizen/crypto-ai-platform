'use client';

import { useCallback, useRef, useState } from 'react';

type Props = {
  symbol: string;
  apiBase: string;
  onNavigate: (module: 'overview'|'market'|'council'|'twin'|'memory'|'lab'|'execution'|'audit') => void;
};

const commands: Record<string, Props['onNavigate'] extends (m: infer M) => any ? M : never> = {
  overview: 'overview', market: 'market', council: 'council', twin: 'twin', memory: 'memory', lab: 'lab', execution: 'execution', audit: 'audit'
};

export default function VoiceTrader({ symbol, apiBase, onNavigate }: Props) {
  const [listening, setListening] = useState(false);
  const [busy, setBusy] = useState(false);
  const [heard, setHeard] = useState('');
  const [reply, setReply] = useState('Voice trader ready.');
  const recognitionRef = useRef<any>(null);

  const speak = useCallback((text: string) => {
    if (typeof window === 'undefined' || !(window as any).speechSynthesis) return;
    (window as any).speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text.slice(0, 900));
    utterance.rate = 1.02;
    utterance.pitch = 1;
    (window as any).speechSynthesis.speak(utterance);
  }, []);

  const runCommand = useCallback(async (raw: string) => {
    const text = raw.trim().toLowerCase();
    if (!text) return;
    setHeard(raw);

    for (const [name, module] of Object.entries(commands)) {
      if (text.includes(name)) {
        onNavigate(module as any);
        const message = `Opening ${name} for ${symbol}.`;
        setReply(message);
        speak(message);
        return;
      }
    }

    if (text.includes('analyze') || text.includes('analysis') || text.includes('signal') || text.includes('market')) {
      setBusy(true);
      try {
        const response = await fetch(`${apiBase}/api/intel/${encodeURIComponent(symbol)}`, { cache: 'no-store' });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(data?.detail || `HTTP ${response.status}`);
        const summary = data?.summary || data?.decision || data?.recommendation || data?.regime || 'Verified intelligence returned, but no short spoken summary was provided.';
        const message = `${symbol}: ${String(summary).replace(/[\n\r]+/g, ' ').slice(0, 700)}`;
        setReply(message);
        speak(message);
      } catch (error) {
        const message = `I could not verify live intelligence for ${symbol}. The system remains fail-closed.`;
        setReply(message);
        speak(message);
      } finally {
        setBusy(false);
      }
      return;
    }

    if (text.includes('stop') || text.includes('quiet') || text.includes('mute')) {
      if (typeof window !== 'undefined' && (window as any).speechSynthesis) (window as any).speechSynthesis.cancel();
      setReply('Voice output stopped.');
      return;
    }

    const message = 'I understood the voice command, but I will not place a trade from an ambiguous instruction. Say analyze market, or name a command layer.';
    setReply(message);
    speak(message);
  }, [apiBase, onNavigate, speak, symbol]);

  const startListening = useCallback(() => {
    if (typeof window === 'undefined') return;
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      const message = 'Voice recognition is not supported by this browser. Use a current Chrome-based browser or the text controls.';
      setReply(message);
      speak(message);
      return;
    }

    if (recognitionRef.current) recognitionRef.current.abort();
    const recognition = new SpeechRecognition();
    recognition.lang = 'en-IN';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    recognition.onstart = () => setListening(true);
    recognition.onend = () => setListening(false);
    recognition.onerror = () => {
      setListening(false);
      setReply('Voice input failed. No trading action was taken.');
    };
    recognition.onresult = (event: any) => {
      const transcript = event.results?.[0]?.[0]?.transcript || '';
      void runCommand(transcript);
    };
    recognitionRef.current = recognition;
    recognition.start();
  }, [runCommand, speak]);

  return (
    <div className="voice-trader glass" aria-label="Voice trader control">
      <div className="voice-trader-copy">
        <span className="kicker">VOICE COMMAND</span>
        <b>{listening ? 'LISTENING…' : busy ? 'ANALYZING…' : 'VOICE READY'}</b>
        <small>{heard ? `Heard: ${heard}` : reply}</small>
      </div>
      <button className={`voice-button ${listening ? 'active' : ''}`} onClick={startListening} disabled={busy} aria-label="Start voice command">
        {listening ? '■' : '🎙'}
      </button>
    </div>
  );
}
