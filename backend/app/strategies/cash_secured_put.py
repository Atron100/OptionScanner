from datetime import date

from app.schemas.market_data import ChainSnapshotResponse, ContractQuoteResponse
from app.strategies.analytics import cash_secured_put_return_on_capital, score_cash_secured_put, short_put_probability_of_profit
from app.strategies.base import CONTRACT_MULTIPLIER, Strategy, StrategyCandidate, StrategyManagementRule


class CashSecuredPutStrategy(Strategy):
    name = "cash_secured_put"

    def generate(self, chain: ChainSnapshotResponse) -> list[StrategyCandidate]:
        candidates: list[StrategyCandidate] = []
        for quote in chain.contracts:
            if quote.right != "P" or quote.expiration_date < date.today():
                continue
            credit = quote.bid if quote.bid is not None else quote.mark
            if credit is None or credit <= 0 or credit >= quote.strike:
                continue
            candidate = self._build_candidate(chain.symbol, quote, credit)
            candidate.score = self.score(candidate)
            candidates.append(candidate)
        return sorted(candidates, key=lambda item: item.score, reverse=True)

    def score(self, candidate: StrategyCandidate) -> float:
        return score_cash_secured_put(candidate)

    def payoff(self, candidate: StrategyCandidate) -> list[tuple[float, float]]:
        max_price = max(candidate.strike * 1.3, candidate.break_even * 1.5)
        step = max_price / 24
        return [
            (
                round(price, 4),
                round((candidate.credit - max(candidate.strike - price, 0)) * CONTRACT_MULTIPLIER, 2),
            )
            for price in (step * index for index in range(25))
        ]

    def adjust(self, candidate: StrategyCandidate) -> list[StrategyManagementRule]:
        return [
            StrategyManagementRule(
                trigger=f"underlying_price <= {candidate.strike:g}",
                action="review_roll_or_assignment",
                rationale="The short put is challenged; compare a defined-risk roll with accepting assignment.",
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
                trigger="assignment_is_no_longer_acceptable",
                action="review_close_or_roll",
                rationale="The cash-secured put thesis requires willingness and capacity to own the shares.",
            ),
        ]

    def _build_candidate(self, symbol: str, quote: ContractQuoteResponse, credit: float) -> StrategyCandidate:
        max_loss_per_share = quote.strike - credit
        candidate = StrategyCandidate(
            strategy=self.name,
            symbol=symbol,
            expiration_date=quote.expiration_date,
            strike=quote.strike,
            credit=credit,
            max_profit=round(credit * CONTRACT_MULTIPLIER, 2),
            max_loss=round(max_loss_per_share * CONTRACT_MULTIPLIER, 2),
            break_even=quote.strike - credit,
            probability_of_profit=short_put_probability_of_profit(quote.delta),
            return_on_capital=cash_secured_put_return_on_capital(quote.strike, credit),
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
