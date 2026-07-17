# OptionScanner

Local-first options research platform built with FastAPI and React.

## Current Capabilities

- FastAPI and React local-development foundation
- SQLite storage for option contracts, quote snapshots, and historical daily bars
- IBKR read-only integration for bounded live option chains, bid/ask/last, Greeks, volume, and open interest
- Targeted live ingestion by exact strike and expiration count
- Historical option-bars endpoint with mocked coverage; live IBKR availability is contract- and data-feed-dependent
- Cash Secured Put candidate generation with payoff, POP estimate, ROC, and liquidity-aware scoring
- Covered Call candidate generation from share count and cost basis, with capped-profit payoff and scoring
- Iron Condor four-leg candidate generation with spot-aware OTM short-leg validation, conservative executable credit, bounded risk, dual break-evens, payoff, and scoring
- Structured adjustment and exit review rules for every generated strategy candidate; no automatic trade execution
- Multi-symbol scanner API with deterministic ranking and POP, ROC, score, EV, and maximum-loss filters
- Responsive React scanner dashboard with quality controls, ranked results, backend status, and mobile support
- Selectable strategy detail panel with responsive payoff chart, leg structure, risk metrics, and lifecycle review rules
- Strategy profit, loss, payoff, and EV values expressed in dollars per standard 100-share option contract; option credit remains quoted per share
- Tracked-stocks panel showing each locally stored symbol's latest price, provider, quote count, and snapshot time, with one-click scanner selection and live Add/Refresh
- Persistent local scan history with recent-run summaries and exact stored result restoration

## Project Layout

- `backend/` - API, config, database, tests
- `frontend/` - React UI, API client, tests
- `data/` - local SQLite database storage
- `md_info/` - roadmap and design documents

## Local Development

### Backend

1. Create a virtual environment.
2. Install backend dependencies from `backend/pyproject.toml`.
3. Run `uvicorn app.main:app --reload --app-dir backend`.

### Frontend

1. Install Node.js 20 or newer.
2. Install frontend dependencies from `frontend/package.json`.
3. Run `npm run dev` from `frontend/`.

### Docker

Run `docker compose up --build`.

## IBKR Market Data

Set `OPTIONSCANNER_MARKET_DATA_PROVIDER=ibkr` and configure the local TWS or IB Gateway endpoint in `.env`. The application is read-only and cancels its temporary market-data subscriptions after collection.

Example targeted live ingestion:

```powershell
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/market-data/ingest" -ContentType "application/json" -Body '{"symbol":"AAPL","strike":315,"expiration_count":5}'
```

Historical bars require that the option contract was previously ingested:

```powershell
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/market-data/historical/ingest" -ContentType "application/json" -Body '{"symbol":"AAPL","expiration_date":"2026-07-10","right":"C","strike":315,"duration_months":1}'
```

IBKR does not provide end-of-day historical data for options. The endpoint requests intraday bars and aggregates them locally by day, but IBKR may still decline a specific option contract when its historical data is unavailable. Confirm the same option has a chart in TWS before relying on an API history request.

Generate Iron Condor candidates from the latest stored chain:

```powershell
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/strategies/iron-condor/generate" -ContentType "application/json" -Body '{"symbol":"OPEN"}' | ConvertTo-Json -Depth 8
```

Scan stored chains and return ranked candidates:

```powershell
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/scanner/scan" -ContentType "application/json" -Body '{"symbols":["OPEN","AAPL"],"strategies":["cash_secured_put","iron_condor"],"minimum_probability_of_profit":0.5,"minimum_days_to_expiration":1,"minimum_credit":0.05,"minimum_open_interest":1,"maximum_loss":500,"limit":20}' | ConvertTo-Json -Depth 10
```
