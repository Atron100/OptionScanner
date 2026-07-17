from datetime import datetime, timezone

import pytest

from app.schemas.market_data import ChainSnapshotResponse, ContractQuoteResponse
from app.strategies.covered_call import CoveredCallStrategy


def test_covered_call_calculates_capped_profit_downside_and_payoff() -> None:
    chain = ChainSnapshotResponse(
        symbol="AAPL",
        provider="mock",
        as_of=datetime.now(timezone.utc),
        quote_count=1,
        contracts=[
            ContractQuoteResponse(
                expiration_date="2026-08-21",
                right="C",
                strike=200,
                bid=4,
                ask=4.2,
                last=4.1,
                mark=4.1,
                implied_volatility=0.25,
                delta=0.3,
                gamma=0.02,
                theta=-0.05,
                vega=0.1,
                open_interest=1000,
                volume=200,
            )
        ],
    )

    candidate = CoveredCallStrategy(shares=100, cost_basis_per_share=190).generate(chain)[0]

    assert candidate.credit == 4
    assert candidate.max_profit == 1400
    assert candidate.max_loss == 18600
    assert candidate.break_even == 186
    assert candidate.probability_of_profit == 0.7
    assert candidate.return_on_capital == pytest.approx(14 / 190, abs=1e-6)
    assert candidate.payoff_points[0][1] == -18600
    assert candidate.payoff_points[-1][1] == 1400
    assert candidate.adjustment_rules[0].action == "review_assignment_or_roll"
    assert candidate.adjustment_rules[0].trigger == "underlying_price >= 200"
    assert candidate.exit_rules[0].trigger == "remaining_option_value <= 2.0000"


def test_covered_call_requires_one_hundred_shares() -> None:
    with pytest.raises(ValueError, match="at least 100 shares"):
        CoveredCallStrategy(shares=99, cost_basis_per_share=190)
