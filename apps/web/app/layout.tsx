import './ui.css';
import VoiceAssistantDock from './components/VoiceAssistantDock';

export const metadata = {
  title: 'IQ200 — Adaptive Market Intelligence',
  description: 'Real-evidence-first AI trading command center.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="en"><body>{children}<VoiceAssistantDock /></body></html>;
}
