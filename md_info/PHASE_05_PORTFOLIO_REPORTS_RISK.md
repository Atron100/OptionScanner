# Phase 5 - Portfolio, Reports, and Risk

## Goal

Expand the platform from a scanner into a research and management tool by adding portfolio awareness, risk summaries, and report exports.

## Scope

- Open position tracking
- Portfolio Greeks aggregation
- Risk metrics
- Alerts and watch conditions
- HTML, Markdown, and Excel report generation

## Planned Deliverables

- portfolio models and services
- aggregate Greek calculations
- open position summary APIs
- report generation services
- frontend portfolio page
- export actions from the UI

## Acceptance Criteria

- Open positions can be stored and displayed
- Portfolio Greeks are computed correctly from sample positions
- Reports can be exported locally in the supported formats
- Risk summary values pass fixture-based tests

## Out of Scope

- Backtesting
- Automation
- Public internet exposure

## Suggested Verification

- Import or create sample positions
- Confirm aggregate risk calculations match expected values
- Generate each supported report format successfully
