export type Theme = 'dark' | 'light';

export const THEME = {
  dark: {
    bg: '#0b0e14', panel: '#151a24', panelBorder: '#232a38',
    text: '#e8ecf4', textMuted: '#8b95a8', accent: '#5b9cff',
    green: '#3ecf8e', red: '#ff5c6c', input: '#1b2230',
  },
  light: {
    bg: '#f4f6fb', panel: '#ffffff', panelBorder: '#e2e6ef',
    text: '#111827', textMuted: '#6b7280', accent: '#2563eb',
    green: '#16a34a', red: '#dc2626', input: '#f1f3f9',
  },
};

export function colors(theme: Theme) {
  return THEME[theme];
}
