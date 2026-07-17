from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.strategies import StrategyCandidateResponse


ScannableStrategy = Literal["cash_secured_put", "iron_condor"]


class ScanRequest(BaseModel):
    symbols: list[str] = Field(min_length=1, max_length=50)
    strategies: list[ScannableStrategy] = Field(
        default_factory=lambda: ["cash_secured_put", "iron_condor"],
        min_length=1,
    )
    minimum_probability_of_profit: float | None = Field(default=None, ge=0, le=1)
    minimum_return_on_capital: float | None = Field(default=None, ge=0)
    minimum_score: float | None = Field(default=None, ge=0, le=100)
    minimum_expected_value: float | None = None
    maximum_loss: float | None = Field(default=None, gt=0)
    minimum_days_to_expiration: int = Field(default=1, ge=0, le=730)
    maximum_days_to_expiration: int | None = Field(default=None, ge=0, le=730)
    minimum_credit: float = Field(default=0.05, ge=0)
    minimum_open_interest: int = Field(default=0, ge=0)
    minimum_volume: int = Field(default=0, ge=0)
    limit: int = Field(default=50, ge=1, le=500)

    @field_validator("symbols")
    @classmethod
    def normalize_symbols(cls, symbols: list[str]) -> list[str]:
        normalized = list(dict.fromkeys(symbol.strip().upper() for symbol in symbols if symbol.strip()))
        if not normalized:
            raise ValueError("At least one non-empty symbol is required.")
        return normalized

    @field_validator("strategies")
    @classmethod
    def deduplicate_strategies(cls, strategies: list[ScannableStrategy]) -> list[ScannableStrategy]:
        return list(dict.fromkeys(strategies))

    @model_validator(mode="after")
    def validate_expiration_range(self):
        if (
            self.maximum_days_to_expiration is not None
            and self.maximum_days_to_expiration < self.minimum_days_to_expiration
        ):
            raise ValueError("maximum_days_to_expiration must be greater than or equal to minimum_days_to_expiration.")
        return self


class RankedScanResult(BaseModel):
    rank: int
    expected_value: float | None
    candidate: StrategyCandidateResponse


class ScanResponse(BaseModel):
    generated_at: datetime
    symbols: list[str]
    strategies: list[ScannableStrategy]
    total_candidates: int
    eligible_candidate_count: int
    filtered_out_count: int
    result_count: int
    warnings: list[str]
    results: list[RankedScanResult]


class ScanHistorySummary(BaseModel):
    id: int
    generated_at: datetime
    symbols: list[str]
    strategies: list[ScannableStrategy]
    total_candidates: int
    result_count: int


class ScanHistoryListResponse(BaseModel):
    count: int
    runs: list[ScanHistorySummary]


class ScanHistoryDetailResponse(BaseModel):
    id: int
    request: ScanRequest
    response: ScanResponse
