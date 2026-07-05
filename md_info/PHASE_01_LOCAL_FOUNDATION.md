# Phase 1 - Local Foundation

## Goal

Create a reliable local web application skeleton that starts cleanly, connects frontend to backend, initializes a database, and has automated tests.

## Scope

- FastAPI backend skeleton
- React frontend skeleton
- SQLite setup
- Config via `.env`
- Docker support
- Backend and frontend test setup
- Local health and system information endpoints

## Planned Deliverables

- `backend/` project scaffold
- `frontend/` project scaffold
- `data/` directory for local SQLite storage
- `.env.example`
- `docker-compose.yml`
- backend health endpoint
- frontend status page connected to backend
- smoke tests for backend and frontend

## Acceptance Criteria

- Backend starts locally without manual patching
- Frontend starts locally without manual patching
- Frontend can call backend successfully
- SQLite file is created automatically
- `docker compose up --build` runs the local stack
- Backend tests pass
- Frontend tests pass

## Out of Scope

- IBKR connectivity
- Option chain download
- Strategy generation
- Scanner logic
- Charts beyond a basic placeholder

## Suggested Verification

- Open the local UI in the browser
- Confirm backend status is healthy
- Confirm config values are loaded correctly
- Run backend unit tests
- Run frontend unit tests
- Start the stack through Docker
