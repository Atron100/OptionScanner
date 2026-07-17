from datetime import date

from app.schemas.market_data import ChainSnapshotResponse, ContractQuoteResponse
from app.strategies.analytics import covered_call_probability_of_profit, covered_call_return_on_capital, score_covered_call
from app.strategies.base import CONTRACT_MULTIPLIER, Strategy, StrategyCandidate, StrategyManagementRule


class CoveredCallStrategy(Strategy):
    name = "covered_call"

    def __init__(self, shares: int, cost_basis_per_share: float) -> None:
        if shares < 100:
            raise ValueError("Covered Call generation requires at least 100 shares.")
        if cost_basis_per_share <= 0:
            raise ValueError("Cost basis per share must be positive.")
        self.shares = shares
        self.cost_basis_per_share = cost_basis_per_share

    def generate(self, chain: ChainSnapshotResponse) -> list[StrategyCandidate]:
        candidates: list[StrategyCandidate] = []
        for quote in chain.contracts:
            if quote.right != "C" or quote.expiration_date < date.today():
                continue
            credit = quote.bid if quote.bid is not None else quote.mark
            if credit is None or credit <= 0:
                continue
            candidate = self._build_candidate(chain.symbol, quote, credit)
            candidate.score = self.score(candidate)
            candidates.append(candidate)
        return sorted(candidates, key=lambda item: item.score, reverse=True)

    def score(self, candidate: StrategyCandidate) -> float:
        return score_covered_call(candidate)

    def payoff(self, candidate: StrategyCandidate) -> list[tuple[float, float]]:
        max_price = max(candidate.strike * 1.3, self.cost_basis_per_share * 1.5)
        step = max_price / 24
        return [
            (
                round(price, 4),
                round(
                    (price - self.cost_basis_per_share + candidate.credit - max(price - candidate.strike, 0))
                    * CONTRACT_MULTIPLIER,
                    2,
                ),
            )
            for price in (step * index for index in range(25))
        ]

    def adjust(self, candidate: StrategyCandidate) -> list[StrategyManagementRule]:
        return [
            StrategyManagementRule(
                trigger=f"underlying_price >= {candidate.strike:g}",
                action="review_assignment_or_roll",
                rationale="The covered call is challenged; compare assignment with a roll before changing the cap.",
            )
        ]

    def exit(self, candidate: StrategyCandidate) -> list[StrategyManagementRule]:
        return [
            StrategyManagementRule(
                trigger=f"remaining_option_value <= {candidate.credit * 0.5:.4f}",
                action="review_close_for_profit",
                rationale="Half of the entry credit has been captured; reassess remaining reward versus risk.",
            ),
            StrategyManagementRule(
                trigger="share_sale_at_strike_is_no_longer_acceptable",
                action="review_close_or_roll",
                rationale="A covered call should remain consistent with the intended share exit price.",
            ),
        ]

    def _build_candidate(self, symbol: str, quote: ContractQuoteResponse, credit: float) -> StrategyCandidate:
        max_profit_per_share = round(quote.strike - self.cost_basis_per_share + credit, 4)
        downside_per_share = round(self.cost_basis_per_share - credit, 4)
        candidate = StrategyCandidate(
            strategy=self.name,
            symbol=symbol,
            expiration_date=quote.expiration_date,
            strike=quote.strike,
            credit=credit,
            max_profit=round(max_profit_per_share * CONTRACT_MULTIPLIER, 2),
            max_loss=round(downside_per_share * CONTRACT_MULTIPLIER, 2),
            break_even=downside_per_share,
            probability_of_profit=covered_call_probability_of_profit(quote.delta),
            return_on_capital=covered_call_return_on_capital(max_profit_per_share, self.cost_basis_per_share),
            score=0,
            implied_volatility=quote.implied_volatility,
            delta=quote.delta,
            open_interest=quote.open_interest,
            volume=quote.volume,
            payoff_points=[],
        )
        candidate.payoff_points = self.payoff(candidate)
        candidate.adjustment_rules = self.adjust(candidate)
        candidate.exit_rules = self.exit(candidate)
        return candidate
