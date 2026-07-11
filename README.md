# OptionScanner

Local-first options research platform built with FastAPI and React.

## Current Capabilities

- FastAPI and React local-development foundation
- SQLite storage for option contracts, quote snapshots, and historical daily bars
- IBKR read-only integration for bounded live option chains, bid/ask/last, Greeks, volume, and open interest
- Targeted live ingestion by exact strike and expiration count
- Historical option-bars endpoint with mocked coverage; live IBKR availability is contract- and data-feed-dependent

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
