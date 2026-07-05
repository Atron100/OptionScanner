# OptionScanner

Local-first options research platform built with FastAPI and React.

## Phase 1 Scope

- FastAPI backend skeleton
- React frontend skeleton
- SQLite configuration
- Docker-based local runtime
- Backend and frontend test harness

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

## Current Environment Note

This repository now contains the Phase 1 scaffold. If local dependencies are not installed yet, startup and test commands will need package installation before they can run successfully.

