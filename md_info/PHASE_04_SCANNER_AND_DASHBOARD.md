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

## Checkpoint 1 - Scanner API

Status: complete and covered by automated backend tests.

- `POST /api/v1/scanner/scan` scans the latest stored snapshots for multiple symbols.
- Cash Secured Put and Iron Condor are supported. Covered Call is excluded until per-symbol holdings and cost basis are available.
- Filters cover minimum POP, ROC, score, expected value, maximum loss, DTE range, credit, open interest, volume, and result limit.
- Quality defaults require at least one DTE and `$0.05` credit; liquidity thresholds default to zero and can be enabled per scan.
- Responses distinguish raw candidates, eligible candidates, filtered candidates, and returned results.
- Ranking is deterministic: strategy score, expected value, POP, ROC, symbol, expiration, then strike.
- Missing snapshots produce warnings without failing results for valid symbols.
- Expected value is a transparent two-outcome estimate: `POP * max_profit - (1 - POP) * max_loss`. It is a ranking aid, not a full probability-distribution model.

## Checkpoint 2 - Scanner Dashboard

Status: complete and covered by frontend interaction tests, a production build, and local desktop/mobile visual QA.

- Responsive React dashboard with backend/database health indicators.
- Multi-symbol and strategy scan controls with POP, DTE, credit, open-interest, volume, and limit inputs.
- Ranked result table with setup, expiration, legs, credit, POP, ROC, score, EV, and liquidity.
- Raw, eligible, filtered, and shown counts plus API warning and empty-result states.
- Local CORS supports both `localhost:5173` and `127.0.0.1:5173`.

## Checkpoint 3 - Strategy Detail and Payoff

Status: implementation and automated verification complete; local populated-state visual acceptance pending.

- Ranked rows open a strategy detail panel, with the first result selected after each scan.
- Responsive SVG payoff chart uses backend-provided payoff points and marks zero P/L and break-even levels.
- Payoff charts use two-decimal strike and P/L axes, green profit segments, and red loss segments; P/L values are dollars per 100-share contract.
- Detail metrics include credit, maximum profit/loss, POP, ROC, and estimated EV.
- Single-leg and four-leg structures render separately with strike, side, price, and liquidity context.
- Adjustment and exit review rules are displayed as read-only lifecycle guidance.
- Detail opening, chart accessibility, lifecycle content, and close behavior are covered by frontend interaction tests.

## Checkpoint 4 - Tracked Stocks Panel

Status: implementation complete; local verification required.

- `GET /api/v1/market-data/underlyings` returns the newest stored snapshot summary for every symbol.
- The dashboard shows latest underlying price, provider, quote count, and snapshot time for each tracked stock.
- Selecting a stock replaces the scanner symbol and clears stale results.
- Add / Refresh ingests five expirations for the first scanner symbol, then reloads the local stock universe.
- Viewing and selecting stored stocks works without TWS; refreshing requires the configured market-data provider.

## Checkpoint 5 - Scan History

Status: implementation complete; local verification required.

- Every successful scan stores its normalized request and exact response in SQLite.
- `GET /api/v1/scanner/history` returns a bounded newest-first summary list.
- `GET /api/v1/scanner/history/{run_id}` restores the immutable request and ranked result without rescanning or contacting IBKR.
- The dashboard lists the ten newest scans and restores supported controls, results, and the first strategy detail.
- History is local research state and does not contain or submit orders.
