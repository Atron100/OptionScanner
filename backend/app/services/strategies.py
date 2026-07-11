from app.schemas.strategies import PayoffPointResponse, StrategyCandidateResponse, StrategyCandidatesResponse
from app.services.market_data import MarketDataQueryService
from app.strategies.cash_secured_put import CashSecuredPutStrategy


class StrategyService:
    def __init__(self, db) -> None:
        self.market_data = MarketDataQueryService(db)

    def generate_cash_secured_puts(self, symbol: str) -> StrategyCandidatesResponse | None:
        chain = self.market_data.get_latest_chain(symbol)
        if chain is None:
            return None

        strategy = CashSecuredPutStrategy()
        candidates = strategy.generate(chain)
        return StrategyCandidatesResponse(
            strategy=strategy.name,
            symbol=chain.symbol,
            candidate_count=len(candidates),
            candidates=[
                StrategyCandidateResponse(
                    strategy=candidate.strategy,
                    symbol=candidate.symbol,
                    expiration_date=candidate.expiration_date,
                    strike=candidate.strike,
                    credit=candidate.credit,
                    max_profit=candidate.max_profit,
                    max_loss=candidate.max_loss,
                    break_even=candidate.break_even,
                    probability_of_profit=candidate.probability_of_profit,
                    return_on_capital=candidate.return_on_capital,
                    score=candidate.score,
                    implied_volatility=candidate.implied_volatility,
                    delta=candidate.delta,
                    open_interest=candidate.open_interest,
                    volume=candidate.volume,
                    payoff_points=[
                        PayoffPointResponse(underlying_price=price, profit_loss=profit_loss)
                        for price, profit_loss in candidate.payoff_points
                    ],
                )
                for candidate in candidates
            ],
        )
