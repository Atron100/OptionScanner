# Options Strategy Scanner & Optimizer

## Objective

Develop a professional options analysis platform that automatically downloads option chain data from Interactive Brokers (IBKR), analyzes multiple option strategies, ranks opportunities using quantitative metrics, generates payoff diagrams, and assists with trade management.

The goal is to create a modular, extensible options platform comparable to professional screening tools while remaining fully under personal control.

---

## Data Source

Primary:
- Interactive Brokers (IBKR)
- IB Gateway (preferred)
- TWS supported

Python:
- ibapi (official)
- ib_insync (optional)

Future providers:
- Polygon.io
- ORATS
- Tradier
- CBOE Data
- OptionMetrics

No web scraping.

---

## Architecture

OptionScanner/

- data/
- database/
- analytics/
- strategies/
- optimizer/
- portfolio/
- reports/
- ui/
- config/
- tests/

---

## Supported Strategies

Income Strategies
- Iron Condor
- Iron Butterfly
- Covered Call (CC)
- Cash Secured Put (CSP)
- Poor Man's Covered Call (PMCC)
- Calendar
- Double Calendar
- Diagonal
- Double Diagonal
- Vertical Credit Spread
- Vertical Debit Spread
- Broken Wing Butterfly
- Butterfly
- Ratio Backspread

Future
- Jade Lizard
- Big Lizard
- Christmas Tree
- Broken Heart

Each strategy should implement:

- generate()
- score()
- payoff()
- adjust()
- exit()

---

## Analytics

Calculate:

Greeks
- Delta
- Gamma
- Theta
- Vega
- Rho

Volatility
- ATM IV
- IV Rank
- IV Percentile
- Historical Volatility
- Skew
- Smile
- Term Structure

Probability
- Probability of Profit
- Expected Value
- Probability Touch

Risk
- ROC
- Margin
- Buying Power
- Assignment Risk

---

## Optimizer

Enumerate all valid strike combinations.

Reject:
- Poor liquidity
- Wide spreads
- High gamma
- Earnings risk
- Low POP

Rank by:
1. Expected Value
2. Return on Capital
3. Probability of Profit
4. Risk

---

## Reports

Generate:
- Excel
- HTML
- Markdown
- PDF (future)

Include:
- Payoff graph
- Greeks
- POP
- ROC
- Expected move
- Score

---

## Dashboard

Display:
- Today's opportunities
- Portfolio Greeks
- IV Rank
- Alerts
- Open positions
- Risk metrics

---

## Roadmap

Phase 1
- IBKR connectivity
- Option chain download
- SQLite

Phase 2
- Iron Condor
- Calendar
- Double Diagonal
- Covered Call
- Cash Secured Put
- Payoff graphs

Phase 3
- Optimizer
- Dashboard
- Scoring

Phase 4
- Portfolio analytics
- Reports
- Risk engine

Phase 5
- Backtesting
- Automation
- AI-assisted recommendations
