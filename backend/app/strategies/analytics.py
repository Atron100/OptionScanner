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


def covered_call_probability_of_profit(delta: float | None) -> float | None:
    if delta is None:
        return None
    return round(max(0.0, min(1.0, 1 - abs(delta))), 4)


def covered_call_return_on_capital(max_profit: float, cost_basis: float) -> float | None:
    if cost_basis <= 0:
        return None
    return round(max_profit / cost_basis, 6)


def score_covered_call(candidate: StrategyCandidate) -> float:
    pop_component = (candidate.probability_of_profit or 0) * 55
    roc_component = min(max(candidate.return_on_capital or 0, 0) * 100, 30)
    liquidity_component = min((candidate.open_interest or 0) / 1000, 10)
    return round(pop_component + roc_component + liquidity_component, 2)


def iron_condor_probability_of_profit(short_put_delta: float | None, short_call_delta: float | None) -> float | None:
    if short_put_delta is None or short_call_delta is None:
        return None
    return round(max(0.0, min(1.0, 1 - abs(short_put_delta) - abs(short_call_delta))), 4)


def iron_condor_return_on_capital(credit: float, max_loss: float) -> float | None:
    if max_loss <= 0:
        return None
    return round(credit / max_loss, 6)


def score_iron_condor(candidate: StrategyCandidate) -> float:
    pop_component = (candidate.probability_of_profit or 0) * 60
    roc_component = min((candidate.return_on_capital or 0) * 100, 30)
    liquidity_component = min((candidate.open_interest or 0) / 1000, 10)
    return round(pop_component + roc_component + liquidity_component, 2)
