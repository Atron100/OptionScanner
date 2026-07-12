from datetime import date
from itertools import combinations

from app.schemas.market_data import ChainSnapshotResponse, ContractQuoteResponse
from app.strategies.analytics import iron_condor_probability_of_profit, iron_condor_return_on_capital, score_iron_condor
from app.strategies.base import Strategy, StrategyCandidate, StrategyLeg


class IronCondorStrategy(Strategy):
    name = "iron_condor"

    def generate(self, chain: ChainSnapshotResponse) -> list[StrategyCandidate]:
        by_expiration: dict[date, list[ContractQuoteResponse]] = {}
        for quote in chain.contracts:
            if quote.expiration_date >= date.today():
                by_expiration.setdefault(quote.expiration_date, []).append(quote)

        candidates: list[StrategyCandidate] = []
        for expiration, quotes in by_expiration.items():
            puts = sorted((quote for quote in quotes if quote.right == "P"), key=lambda quote: quote.strike)
            calls = sorted((quote for quote in quotes if quote.right == "C"), key=lambda quote: quote.strike)
            for long_put, short_put in combinations(puts, 2):
                for short_call, long_call in combinations(calls, 2):
                    if short_put.strike >= short_call.strike:
                        continue
                    candidate = self._build_candidate(chain.symbol, expiration, long_put, short_put, short_call, long_call)
                    if candidate is not None:
                        candidate.score = self.score(candidate)
                        candidates.append(candidate)
        return sorted(candidates, key=lambda item: item.score, reverse=True)

    def score(self, candidate: StrategyCandidate) -> float:
        return score_iron_condor(candidate)

    def payoff(self, candidate: StrategyCandidate) -> list[tuple[float, float]]:
        max_price = max(leg.strike for leg in candidate.legs) * 1.3
        step = max_price / 32
        points: list[tuple[float, float]] = []
        for price in (step * index for index in range(33)):
            profit_loss = candidate.credit
            for leg in candidate.legs:
                intrinsic = max(leg.strike - price, 0) if leg.right == "P" else max(price - leg.strike, 0)
                profit_loss += intrinsic if leg.action == "BUY" else -intrinsic
            points.append((round(price, 4), round(profit_loss, 4)))
        return points

    def _build_candidate(
        self,
        symbol: str,
        expiration: date,
        long_put: ContractQuoteResponse,
        short_put: ContractQuoteResponse,
        short_call: ContractQuoteResponse,
        long_call: ContractQuoteResponse,
    ) -> StrategyCandidate | None:
        if any(
            price is None or price <= 0
            for price in (long_put.ask, short_put.bid, short_call.bid, long_call.ask)
        ):
            return None
        credit = round(short_put.bid + short_call.bid - long_put.ask - long_call.ask, 4)
        if credit <= 0:
            return None

        put_width = short_put.strike - long_put.strike
        call_width = long_call.strike - short_call.strike
        max_loss = round(max(put_width, call_width) - credit, 4)
        if max_loss <= 0:
            return None

        legs = [
            StrategyLeg("BUY", "P", long_put.strike, long_put.ask, long_put.delta),
            StrategyLeg("SELL", "P", short_put.strike, short_put.bid, short_put.delta),
            StrategyLeg("SELL", "C", short_call.strike, short_call.bid, short_call.delta),
            StrategyLeg("BUY", "C", long_call.strike, long_call.ask, long_call.delta),
        ]
        deltas = [leg.delta for leg in legs]
        net_delta = None
        if all(delta is not None for delta in deltas):
            net_delta = round(deltas[0] - deltas[1] - deltas[2] + deltas[3], 6)
        open_interests = [value for value in (long_put.open_interest, short_put.open_interest, short_call.open_interest, long_call.open_interest) if value is not None]
        volumes = [value for value in (long_put.volume, short_put.volume, short_call.volume, long_call.volume) if value is not None]
        short_ivs = [value for value in (short_put.implied_volatility, short_call.implied_volatility) if value is not None]

        candidate = StrategyCandidate(
            strategy=self.name,
            symbol=symbol,
            expiration_date=expiration,
            strike=short_put.strike,
            credit=credit,
            max_profit=credit,
            max_loss=max_loss,
            break_even=round(short_put.strike - credit, 4),
            upper_break_even=round(short_call.strike + credit, 4),
            probability_of_profit=iron_condor_probability_of_profit(short_put.delta, short_call.delta),
            return_on_capital=iron_condor_return_on_capital(credit, max_loss),
            score=0,
            implied_volatility=round(sum(short_ivs) / len(short_ivs), 6) if short_ivs else None,
            delta=net_delta,
            open_interest=min(open_interests) if open_interests else None,
            volume=min(volumes) if volumes else None,
            payoff_points=[],
            legs=legs,
        )
        candidate.payoff_points = self.payoff(candidate)
        return candidate
