# Phase 4 - Scanner and Dashboard

## Goal

Turn strategy generation into a usable local product workflow with ranked scan results and a browser-based dashboard.

## Scope

- Scan request and result APIs
- Ranking and filtering pipeline
- Dashboard page
- Strategy result table
- Strategy detail page
- Payoff chart component
- Basic job history or scan history view

## Planned Deliverables

- scanner service
- ranking rules for EV, ROC, POP, and risk
- frontend dashboard layout
- scan execution controls
- scan results UI
- payoff visualization UI

## Acceptance Criteria

- A user can trigger a scan from the web UI
- Ranked opportunities are shown in the UI
- Filters work consistently
- Strategy detail page shows payoff and scoring data
- Scanner tests and UI tests pass

## Out of Scope

- Full portfolio analytics
- Report exports
- VPS deployment

## Suggested Verification

- Run a local scan for one or more symbols
- Confirm the ranking order is reproducible from fixture data
- Confirm the UI renders result details without manual refresh hacks
