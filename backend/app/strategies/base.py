from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date

from app.schemas.market_data import ChainSnapshotResponse


@dataclass(slots=True)
class StrategyLeg:
    action: str
    right: str
    strike: float
    price: float
    delta: float | None


@dataclass(slots=True)
class StrategyCandidate:
    strategy: str
    symbol: str
    expiration_date: date
    strike: float
    credit: float
    max_profit: float
    max_loss: float
    break_even: float
    probability_of_profit: float | None
    return_on_capital: float | None
    score: float
    implied_volatility: float | None
    delta: float | None
    open_interest: int | None
    volume: int | None
    payoff_points: list[tuple[float, float]]
    upper_break_even: float | None = None
    legs: list[StrategyLeg] = field(default_factory=list)


class Strategy(ABC):
    @abstractmethod
    def generate(self, chain: ChainSnapshotResponse) -> list[StrategyCandidate]:
        raise NotImplementedError

    @abstractmethod
    def score(self, candidate: StrategyCandidate) -> float:
        raise NotImplementedError

    @abstractmethod
    def payoff(self, candidate: StrategyCandidate) -> list[tuple[float, float]]:
        raise NotImplementedError
