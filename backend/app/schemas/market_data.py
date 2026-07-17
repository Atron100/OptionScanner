from datetime import date, datetime

from pydantic import BaseModel, Field


class IngestChainRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=32)
    strike: float | None = Field(default=None, gt=0)
    expiration_count: int | None = Field(default=None, ge=1, le=10)


class IngestChainResponse(BaseModel):
    symbol: str
    provider: str
    snapshot_id: int
    contract_count: int
    quote_count: int
    expirations: list[date]
    as_of: datetime
    underlying_price: float | None = None
    warnings: list[str] = Field(default_factory=list)


class ContractQuoteResponse(BaseModel):
    expiration_date: date
    right: str
    strike: float
    bid: float | None
    ask: float | None
    last: float | None
    mark: float | None
    implied_volatility: float | None
    delta: float | None
    gamma: float | None
    theta: float | None
    vega: float | None
    open_interest: int | None
    volume: int | None


class ChainSnapshotResponse(BaseModel):
    symbol: str
    provider: str
    as_of: datetime
    underlying_price: float | None = None
    quote_count: int
    contracts: list[ContractQuoteResponse]


class UnderlyingSummaryResponse(BaseModel):
    symbol: str
    name: str | None
    provider: str
    underlying_price: float | None
    as_of: datetime
    quote_count: int


class TrackedUnderlyingsResponse(BaseModel):
    count: int
    underlyings: list[UnderlyingSummaryResponse]


class IngestHistoricalBarsRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=32)
    expiration_date: date
    right: str = Field(pattern="^[CPcp]$")
    strike: float = Field(gt=0)
    duration_months: int = Field(default=1, ge=1, le=3)


class HistoricalBarResponse(BaseModel):
    bar_date: date
    open: float
    high: float
    low: float
    close: float
    volume: int | None


class HistoricalBarsResponse(BaseModel):
    symbol: str
    expiration_date: date
    right: str
    strike: float
    provider: str
    bar_count: int
    bars: list[HistoricalBarResponse]
