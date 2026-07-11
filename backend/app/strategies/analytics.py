from app.strategies.base import StrategyCandidate


def short_put_probability_of_profit(delta: float | None) -> float | None:
    if delta is None:
        return None
    return round(max(0.0, min(1.0, 1 - abs(delta))), 4)


def cash_secured_put_return_on_capital(strike: float, credit: float) -> float | None:
    capital_at_risk = strike - credit
    if capital_at_risk <= 0:
        return None
    return round(credit / capital_at_risk, 6)


def score_cash_secured_put(candidate: StrategyCandidate) -> float:
    pop_component = (candidate.probability_of_profit or 0) * 60
    roc_component = min((candidate.return_on_capital or 0) * 100, 25)
    liquidity_component = min((candidate.open_interest or 0) / 1000, 10)
    return round(pop_component + roc_component + liquidity_component, 2)
