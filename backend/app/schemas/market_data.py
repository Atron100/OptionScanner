from datetime import date, datetime

from pydantic import BaseModel, Field


class IngestChainRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=32)


class IngestChainResponse(BaseModel):
    symbol: str
    provider: str
    snapshot_id: int
    contract_count: int
    quote_count: int
    expirations: list[date]
    as_of: datetime
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
    quote_count: int
    contracts: list[ContractQuoteResponse]
