# Phase 3 - Strategy Engine v1

## Goal

Introduce the reusable strategy architecture and implement the first production-ready strategy set on top of stored market data.

## Scope

- Strategy interface and plugin-style structure
- Shared analytics helpers used across strategies
- First supported strategies:
  - Iron Condor
  - Covered Call
  - Cash Secured Put
- Basic payoff data generation
- Basic strategy scoring inputs

## Planned Deliverables

- strategy base interface with:
  - `generate()`
  - `score()`
  - `payoff()`
  - `adjust()`
  - `exit()`
- analytics helpers for POP, ROC, break-even, and risk bounds
- strategy result schema for API responses
- unit tests for each strategy

## Acceptance Criteria

- Each v1 strategy can generate valid candidates from stored chains
- Each strategy can return a normalized score payload
- Payoff data can be returned in a chart-ready structure
- Deterministic strategy tests pass from fixture data

## Out of Scope

- Full optimizer
- Portfolio risk engine
- Multi-broker support
- Automated trade execution

## Suggested Verification

- Generate candidates for a known sample chain
- Compare strategy outputs against expected fixtures
- Confirm invalid combinations are rejected cleanly
