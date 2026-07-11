from datetime import datetime, timezone

import pytest

from app.schemas.market_data import ChainSnapshotResponse, ContractQuoteResponse
from app.strategies.cash_secured_put import CashSecuredPutStrategy


def test_cash_secured_put_calculates_risk_profit_and_payoff() -> None:
    chain = ChainSnapshotResponse(
        symbol="AAPL",
        provider="mock",
        as_of=datetime.now(timezone.utc),
        quote_count=1,
        contracts=[
            ContractQuoteResponse(
                expiration_date="2026-08-21",
                right="P",
                strike=200,
                bid=4,
                ask=4.2,
                last=4.1,
                mark=4.1,
                implied_volatility=0.25,
                delta=-0.3,
                gamma=0.02,
                theta=-0.05,
                vega=0.1,
                open_interest=1000,
                volume=200,
            )
        ],
    )

    candidate = CashSecuredPutStrategy().generate(chain)[0]

    assert candidate.credit == 4
    assert candidate.max_profit == 4
    assert candidate.max_loss == 196
    assert candidate.break_even == 196
    assert candidate.probability_of_profit == 0.7
    assert candidate.return_on_capital == pytest.approx(4 / 196, abs=1e-6)
    assert candidate.score > 0
    assert candidate.payoff_points[0][1] == -196
    assert candidate.payoff_points[-1][1] == 4
