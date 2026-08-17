# Local setup — V0.2

## Backend
```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

## Web
```bash
cd apps/web
npm install
npm run dev
```

Open the Next.js page and analyze BTCUSDT/ETHUSDT/SOLUSDT.

The backend uses Binance's public market-data endpoint in this development version, so no Binance API key is required for this public-data demo.

## Important
- Live trading remains disabled.
- Do not put API secrets in frontend code.
- Do not enable withdrawal permissions.
- Real order execution must be implemented and tested separately against current official Binance API documentation.
