from datetime import date

from pydantic import BaseModel, Field


class GenerateCashSecuredPutRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=32)


class GenerateCoveredCallRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=32)
    shares: int = Field(ge=100)
    cost_basis_per_share: float = Field(gt=0)


class GenerateIronCondorRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=32)


class PayoffPointResponse(BaseModel):
    underlying_price: float
    profit_loss: float


class StrategyLegResponse(BaseModel):
    action: str
    right: str
    strike: float
    price: float
    delta: float | None


class StrategyCandidateResponse(BaseModel):
    strategy: str
    symbol: str
    expiration_date: date
    strike: float
    credit: float
    max_profit: float
    max_loss: float
    break_even: float
    upper_break_even: float | None = None
    probability_of_profit: float | None
    return_on_capital: float | None
    score: float
    implied_volatility: float | None
    delta: float | None
    open_interest: int | None
    volume: int | None
    payoff_points: list[PayoffPointResponse]
    legs: list[StrategyLegResponse] = Field(default_factory=list)


class StrategyCandidatesResponse(BaseModel):
    strategy: str
    symbol: str
    candidate_count: int
    candidates: list[StrategyCandidateResponse]
