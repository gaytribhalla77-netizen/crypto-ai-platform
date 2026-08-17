# V1.7 — Dashboard features (this pass)

## Fixed / connected (backend)
- **News engine was regressed** in this branch — `backend/news/engine.py` had
  become a bare JSON-feed stub with no real RSS parsing and no sentiment
  scoring. Restored the working RSS/Atom parser + transparent keyword-count
  sentiment, and re-added `GET /api/news/{symbol}` (`backend/api/news_routes.py`),
  which had been dropped from `main.py` entirely.
- **Stop-loss/take-profit was dead code.** `database/models.Position` and
  `trading/position_worker.PositionWorker` (used by the `position_monitor`
  background worker) already existed, but nothing ever created a `Position`
  row when an order filled — so there was never anything for the monitor to
  watch. `trading/testnet_service.py` now creates a `Position` (with the
  risk engine's computed SL/TP prices) on a filled BUY, and closes the
  oldest open position for that symbol on a filled SELL.
- `ProductionRiskManager` / `RiskEngine` now read `DEFAULT_STOP_LOSS_PERCENT`
  / `DEFAULT_TAKE_PROFIT_PERCENT` from `.env` (they were hardcoded 5/5
  before), and accept a **per-order override** (`stop_loss_pct`,
  `take_profit_pct`) — this is what powers the "how much should I risk?"
  prompt in the buy/sell form.

## New (backend)
- `backend/api/dashboard_routes.py` (`/api/dashboard/...`):
  - `GET /history` — order history/journal for the logged-in user.
  - `GET /positions` — open positions with a live SL/TP evaluation.
  - `GET /portfolio` — invested vs. current value vs. unrealized P&L, at
    live market price.
  - `GET /watchlist?symbols=...` — price + 24h change + news sentiment for
    several coins in one call (defaults to `WATCHLIST_SYMBOLS` in `.env`).
  - `GET /klines/{symbol}` — candlestick data for the chart.
- News feeds expanded from 3 to 8 (added CryptoSlate, NewsBTC, The Block,
  Bitcoin Magazine, r/CryptoCurrency) and coins from 6 to 14.
- CORS enabled in `main.py` so the Next.js dev server (localhost:3000) can
  call the API (localhost:8000).

## New (frontend — `apps/web`)
`apps/web` had only a placeholder single-button page and was missing
`app/layout.tsx` and `tsconfig.json` (would not have run as-is). Added:
- `app/layout.tsx`, `tsconfig.json` — required Next.js scaffolding.
- `app/lib/api.ts`, `i18n.ts`, `theme.ts` — API client, Hindi/English
  strings, dark/light color tokens.
- `app/components/`: `AuthPanel`, `Watchlist`, `PriceChart` (plain-SVG
  candlesticks, no chart library needed), `TradeForm` (buy/sell with the
  SL/TP % prompt), `OrderHistory`, `PortfolioSummary`, `PriceAlerts`
  (browser Notification API, client-side only — free, no backend needed),
  `NewsPanel`.
- `app/page.tsx` — composes everything, with a theme toggle and a
  Hindi ⇄ English switch (`localStorage`-persisted).

## Not done — needs a paid key or is a separate, larger piece of work
- **Real AI analysis**: `ai/providers/openai_provider.py` already exists and
  activates automatically once `AI_API_KEY` is set in `.env` — no code
  change needed on your end, just the key.
- **Telegram bot control**: `backend/telegram/bot.py` is a placeholder.
  Wiring it up (long-polling or webhook, plus `TELEGRAM_ALLOWED_USER_IDS`
  from `.env`) is free but is its own task — didn't fold it into this pass.

# V1.8 — Voice control (this pass)

Uses only free browser APIs — no paid key required for the basic version.

## New (backend)
- `backend/voice/service.py` — rewritten from a pass-through stub into a
  real (keyword-based) Hinglish intent parser. Recognizes: price, watchlist,
  portfolio, positions, history, news, and buy/sell trade commands, plus
  confirm/cancel. Reuses `news.engine.ASSET_KEYWORDS` so "bitcoin"/"btc"
  resolve the same way everywhere.
  **Trade intents always return `requires_confirmation: true` and this
  service never touches the database or an exchange** — it only classifies
  text. Executing a trade still has to go through the normal authenticated,
  risk-gated `/api/v06/testnet/order` endpoint.
- `backend/api/voice_routes.py` — `POST /api/voice/parse` (public,
  stateless): `{"text": "..."}` in, structured intent out.

## New (frontend)
- `apps/web/app/components/VoiceControl.tsx` — mic button using the
  browser's built-in `SpeechRecognition` (Chrome/Edge, free) for
  speech-to-text, and `speechSynthesis` (free) to read answers back.
  - Read-only commands (price/watchlist/portfolio/positions/history/news)
    run immediately and are spoken back.
  - Buy/sell commands show a **Yes/No confirmation card** (and accept a
    spoken "confirm"/"cancel" as an alternative to tapping) before ever
    calling the order endpoint — nothing executes on the first utterance.
  - Wired into `app/page.tsx`, next to the trade form.

## Known limits (be aware of these)
- `SpeechRecognition` is a **Chrome/Edge-only** browser API — it won't work
  in Firefox or Safari. There's no server-side speech recognition in this
  build, so those browsers currently can't use voice at all.
- Recognition language is fixed to `en-IN`, not `hi-IN` — that transcribes
  code-switched Hindi/English speech into Latin script most reliably, which
  is what the keyword parser expects. Pure Hindi in Devanagari script
  won't match.
- The intent parser is keyword-matching, not a real NLU model — it won't
  understand phrasing outside the patterns in `voice/service.py`. For
  broader natural-language understanding you'd want to route through
  `AI_API_KEY` (see the AI analysis note above) instead of extending the
  keyword list indefinitely.
- Amount is parsed as "the first number in the sentence" — a sentence with
  two numbers ("buy 50 dollar bitcoin at 3 pm") could pick the wrong one.
  Always read back the confirmation card before saying "confirm".


## How to run
```
# backend
cd backend && pip install -r requirements.txt
uvicorn main:app --reload --app-dir . 2>/dev/null || uvicorn main:app --reload

# frontend (separate terminal)
cd apps/web && cp .env.local.example .env.local && npm install && npm run dev
```
Then open http://localhost:3000. See `docs/deployment/LOCAL_SETUP.md` for
the full original setup (DB, Docker) — nothing there changed.

# V1.9 — Real trained AI model (this pass)

This is a genuinely trained statistical model (scikit-learn), not an LLM
wrapper — and, per what was asked, it tracks whether its own predictions
were actually right, instead of just asserting confidence.

## Be realistic about what this is
Short-horizon crypto price direction is extremely hard to predict — markets
are close to efficient, so most honest backtests land near a 50-55%
accuracy, barely above a coin flip. `ai/ml/train.py` prints the accuracy
against a **naive baseline** (always guessing the majority class) precisely
so you can see whether the model is finding any real edge at all, or is
just noise. Don't deploy a model whose accuracy isn't clearly above that
baseline. This is standard, expected behavior for this kind of problem —
not a bug in the pipeline.

## New (backend)
- `database/models.Prediction` + `PredictionRepository` — every prediction
  is stored *before* the outcome is known, then resolved later against the
  real price. This is what makes "was it right" a checked fact, not a
  claim.
- `ai/ml/features.py` — shared feature engineering (returns, RSI, moving-
  average ratios, volatility, volume z-score, Bollinger width) used by both
  training and inference, so they can't silently drift apart.
- `ai/ml/train.py` — **run this yourself, manually, before predictions will
  work**:
  ```
  cd backend
  pip install -r requirements.txt
  python -m ai.ml.train --symbol BTCUSDT --interval 15m --horizon 4
  ```
  Fetches real historical klines, does a **time-based** train/test split
  (not random — random splits leak the future into training for time
  series), trains a `LogisticRegression`, and prints honest backtest
  accuracy/precision/recall plus the naive baseline. Saves the model to
  `ai/ml/models/`. Repeat per symbol/interval/horizon you want.
- `ai/ml/predictor.py` — loads a trained model and predicts; returns
  `NOT_TRAINED` (not a guess) if you haven't trained one for that
  symbol/interval/horizon yet. Also resolves due predictions against the
  live price.
- `api/ml_routes.py`:
  - `POST /api/ml/predict/{symbol}` — runs the model, logs the prediction.
  - `GET /api/ml/accuracy/{symbol}` — the model's live, ongoing track
    record from resolved predictions. This is the number that answers
    "does it know if it was right or wrong" — computed independently from
    stored outcomes, not self-reported.
- `market/binance_public.py` — added `klines_history()` (pages past the
  1000-candle single-call limit) for building a larger training set.

## New (frontend)
- `apps/web/app/components/AIPrediction.tsx` — "Get Prediction" button,
  shows direction + confidence + the model's backtest accuracy, and below
  it the **live accuracy** from `/api/ml/accuracy`. Always shows a
  "not financial advice" disclaimer. Wired into `app/page.tsx`.

## What this does not do
- It does not auto-trade on its own predictions. Nothing in `ai/ml/`
  calls the order endpoint. Wiring predictions into automated execution
  would be a further, separate, much higher-stakes step — not something
  to enable without a lot more validation.
- It is symbol/interval/horizon-specific — training on BTCUSDT 15m/4
  candles does not give you a model for ETHUSDT or for a 1h horizon; train
  each one you actually want to use.
