# Phase 2 - Market Data Core

## Goal

Build the backend data model and broker integration foundation needed to fetch, normalize, and store option chain data locally.

## Scope

- Domain models for underlyings, expirations, option contracts, quotes, and snapshots
- Database migrations for market data entities
- IBKR connection manager
- Market data service abstraction
- Manual chain ingestion flow for selected symbols

## Planned Deliverables

- backend models for market data
- repository or service layer for persistence
- IBKR config structure
- connection health endpoint or status service
- option chain ingestion service
- initial sample data fixtures for tests

## Acceptance Criteria

- Database schema supports stored option chains and quote snapshots
- A manual request can trigger chain ingestion for a symbol
- Data is normalized and persisted in SQLite
- Mocked broker tests pass without requiring a live session
- Optional live connectivity test works against local IB Gateway or TWS

## Out of Scope

- Strategy generation
- Portfolio analytics
- Opportunity ranking
- Production deployment

## Suggested Verification

- Ingest one symbol successfully
- Re-run ingestion without corrupting data
- Confirm contract and quote records are queryable
- Run mocked integration tests for the broker adapter
