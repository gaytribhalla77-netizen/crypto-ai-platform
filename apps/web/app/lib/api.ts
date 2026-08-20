export const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

export function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return window.sessionStorage.getItem('access_token');
}

export function setToken(token: string | null) {
  if (typeof window === 'undefined') return;
  if (token) window.sessionStorage.setItem('access_token', token);
  else window.sessionStorage.removeItem('access_token');
}

async function request(path: string, opts: RequestInit = {}, auth = false) {
  const headers: Record<string, string> = { ...(opts.headers as any) };
  if (auth) {
    const token = getToken();
    if (!token) throw new Error('AUTH_REQUIRED');
    headers['Authorization'] = `Bearer ${token}`;
  }
  const res = await fetch(`${API_BASE}${path}`, { ...opts, headers });
  if (!res.ok) {
    let detail = res.statusText;
    try { const body = await res.json(); detail = body.detail || JSON.stringify(body); } catch {}
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
  }
  return res.json();
}

function qs(params: Record<string, any>) {
  const p = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => { if (v !== undefined && v !== null && v !== '') p.set(k, String(v)); });
  const s = p.toString();
  return s ? `?${s}` : '';
}

export const api = {
  register: (email: string, password: string) => request(`/api/auth/register`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email, password }) }),
  login: (email: string, password: string) => request(`/api/auth/login`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email, password }) }),
  market: (symbol: string) => request(`/api/market/${symbol}`),
  news: (symbol: string) => request(`/api/news/${symbol}`),
  watchlist: (symbols?: string[]) => request(`/api/dashboard/watchlist${qs({ symbols: symbols?.join(',') })}`),
  klines: (symbol: string, interval = '15m', limit = 100) => request(`/api/dashboard/klines/${symbol}${qs({ interval, limit })}`),
  intel: (symbol: string) => request(`/api/intel/${symbol}`),
  history: (limit = 100) => request(`/api/dashboard/history${qs({ limit })}`, {}, true),
  positions: () => request(`/api/dashboard/positions`, {}, true),
  portfolio: () => request(`/api/dashboard/portfolio`, {}, true),
  voiceParse: (text: string) => request(`/api/voice/parse`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text }) }),
  securityAuditScan: (target: string, authorization: string) => request(`/api/security-audit/scan`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ target, authorization })
  }, true),
  mlPredict: (symbol: string) => request(`/api/ml/predict/${symbol}`, { method: 'POST' }),
  mlAccuracy: (symbol: string) => request(`/api/ml/accuracy/${symbol}`),
  placeOrder: (params: { symbol: string; side: 'BUY' | 'SELL'; amount_usdt: number; price: number; quantity: number; stop_loss_pct?: number; take_profit_pct?: number; client_request_id?: string; totp_code?: string; live?: boolean; }) => params.live
    ? request('/api/real/binance/order', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ symbol: params.symbol, side: params.side, quantity: params.quantity, totp_code: params.totp_code, client_request_id: params.client_request_id }) }, true)
    : request(`/api/v06/testnet/order${qs(params)}`, { method: 'POST' }, true),
};
