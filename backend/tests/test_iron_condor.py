from datetime import datetime, timezone

from app.schemas.market_data import ChainSnapshotResponse, ContractQuoteResponse
from app.strategies.iron_condor import IronCondorStrategy


def _quote(right: str, strike: float, bid: float, ask: float, delta: float) -> ContractQuoteResponse:
    return ContractQuoteResponse(
        expiration_date="2026-08-21",
        right=right,
        strike=strike,
        bid=bid,
        ask=ask,
        last=(bid + ask) / 2,
        mark=(bid + ask) / 2,
        implied_volatility=0.25,
        delta=delta,
        gamma=0.02,
        theta=-0.05,
        vega=0.1,
        open_interest=1000,
        volume=200,
    )


def test_iron_condor_builds_bounded_four_leg_credit_spread() -> None:
    chain = ChainSnapshotResponse(
        symbol="TEST",
        provider="mock",
        as_of=datetime.now(timezone.utc),
        underlying_price=100,
        quote_count=4,
        contracts=[
            _quote("P", 90, 0.9, 1.0, -0.1),
            _quote("P", 95, 2.5, 2.6, -0.2),
            _quote("C", 105, 2.5, 2.6, 0.2),
            _quote("C", 110, 0.9, 1.0, 0.1),
        ],
    )

    candidate = IronCondorStrategy().generate(chain)[0]

    assert [(leg.action, leg.right, leg.strike) for leg in candidate.legs] == [
        ("BUY", "P", 90),
        ("SELL", "P", 95),
        ("SELL", "C", 105),
        ("BUY", "C", 110),
    ]
    assert candidate.credit == 3
    assert candidate.max_profit == 300
    assert candidate.max_loss == 200
    assert candidate.break_even == 92
    assert candidate.upper_break_even == 108
    assert candidate.probability_of_profit == 0.6
    assert candidate.return_on_capital == 1.5
    assert candidate.payoff_points[0][1] == -200
    assert candidate.payoff_points[-1][1] == -200
    assert max(point[1] for point in candidate.payoff_points) == 300
    assert candidate.adjustment_rules[0].trigger == "underlying_price <= 95 or underlying_price >= 105"
    assert candidate.exit_rules[0].trigger == "remaining_spread_value <= 1.5000"
    assert candidate.exit_rules[1].trigger == "unrealized_loss >= 3.0000"


def test_iron_condor_rejects_non_executable_credit() -> None:
    chain = ChainSnapshotResponse(
        symbol="TEST",
        provider="mock",
        as_of=datetime.now(timezone.utc),
        underlying_price=100,
        quote_count=4,
        contracts=[
            _quote("P", 90, 1.9, 2.0, -0.1),
            _quote("P", 95, 1.0, 1.1, -0.2),
            _quote("C", 105, 1.0, 1.1, 0.2),
            _quote("C", 110, 1.9, 2.0, 0.1),
        ],
    )

    assert IronCondorStrategy().generate(chain) == []


def test_iron_condor_rejects_short_legs_that_do_not_surround_underlying() -> None:
    chain = ChainSnapshotResponse(
        symbol="TEST",
        provider="mock",
        as_of=datetime.now(timezone.utc),
        underlying_price=89,
        quote_count=4,
        contracts=[
            _quote("P", 90, 0.9, 1.0, -0.1),
            _quote("P", 95, 2.5, 2.6, -0.2),
            _quote("C", 105, 2.5, 2.6, 0.2),
            _quote("C", 110, 0.9, 1.0, 0.1),
        ],
    )

    assert IronCondorStrategy().generate(chain) == []
