# OptionScanner Phased Build Plan

This project will use:

- Backend: FastAPI
- Frontend: React + Vite + TypeScript
- Database: SQLite for local development and initial single-user deployment
- Deployment target: local first, VPS last

## Delivery Rules

- Build and verify each phase locally before starting the next one.
- Keep each phase small enough to test clearly.
- Do not mix future-phase features into the current phase unless required for stability.
- Prefer reusable backend APIs over UI-specific logic.

## Phase Order

1. [Phase 1 - Local Foundation](./PHASE_01_LOCAL_FOUNDATION.md)
2. [Phase 2 - Market Data Core](./PHASE_02_MARKET_DATA_CORE.md)
3. [Phase 3 - Strategy Engine v1](./PHASE_03_STRATEGY_ENGINE_V1.md)
4. [Phase 4 - Scanner and Dashboard](./PHASE_04_SCANNER_AND_DASHBOARD.md)
5. [Phase 5 - Portfolio, Reports, and Risk](./PHASE_05_PORTFOLIO_REPORTS_RISK.md)
6. [Phase 6 - Hardening and VPS Deployment](./PHASE_06_HARDENING_AND_VPS.md)

## Project Principles

- Local-first development
- Clean API boundaries
- Modular strategy design
- Testability before feature breadth
- Docker-compatible runtime from early phases

## Initial v1 Scope

- Single-user application
- Interactive Brokers as the first provider
- No web scraping
- Manual scan execution first
- No live order execution in early phases
- VPS deployment only after local validation is complete
