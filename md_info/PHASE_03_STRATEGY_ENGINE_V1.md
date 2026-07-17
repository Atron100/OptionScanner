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

## Verified Checkpoint

- Reusable `Strategy` interface and shared analytics helpers added.
- Cash Secured Put generation is implemented against the latest stored chain.
- Covered Call generation is implemented with required share count and per-share cost basis inputs.
- Iron Condor generation is implemented as a four-leg credit spread with validated leg ordering, conservative bid/ask execution, bounded loss, and dual break-evens.
- Live chain discovery is centered on the stored underlying price, and Iron Condors require the short put below spot and short call above spot.
- The common strategy interface now implements `generate()`, `score()`, `payoff()`, `adjust()`, and `exit()`.
- Candidate API responses include normalized adjustment and exit review rules with a trigger, action, and rationale.
- Lifecycle rules are research guidance only; order execution and position-aware evaluation remain out of scope.
- Each candidate returns credit, maximum profit/loss, break-even, POP estimate, ROC, liquidity inputs, score, and chart-ready payoff points.
- Mocked unit and API tests cover all three strategies; local CSP and Covered Call responses were also verified against stored chains.
- Expired contracts are excluded from new CSP candidates.
- Phase 3 acceptance criteria are complete. Next phase: Phase 4 Scanner and Dashboard.
