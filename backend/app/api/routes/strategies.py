from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.strategies import (
    GenerateCashSecuredPutRequest,
    GenerateCoveredCallRequest,
    GenerateIronCondorRequest,
    StrategyCandidatesResponse,
)
from app.services.strategies import StrategyService

router = APIRouter(prefix="/strategies")


@router.post("/cash-secured-put/generate", response_model=StrategyCandidatesResponse)
def generate_cash_secured_puts(
    payload: GenerateCashSecuredPutRequest,
    db: Session = Depends(get_db),
) -> StrategyCandidatesResponse:
    result = StrategyService(db).generate_cash_secured_puts(payload.symbol)
    if result is None:
        raise HTTPException(status_code=404, detail=f"No chain snapshot found for symbol '{payload.symbol.upper()}'")
    return result


@router.post("/covered-call/generate", response_model=StrategyCandidatesResponse)
def generate_covered_calls(
    payload: GenerateCoveredCallRequest,
    db: Session = Depends(get_db),
) -> StrategyCandidatesResponse:
    result = StrategyService(db).generate_covered_calls(
        payload.symbol,
        payload.shares,
        payload.cost_basis_per_share,
    )
    if result is None:
        raise HTTPException(status_code=404, detail=f"No chain snapshot found for symbol '{payload.symbol.upper()}'")
    return result


@router.post("/iron-condor/generate", response_model=StrategyCandidatesResponse)
def generate_iron_condors(
    payload: GenerateIronCondorRequest,
    db: Session = Depends(get_db),
) -> StrategyCandidatesResponse:
    result = StrategyService(db).generate_iron_condors(payload.symbol)
    if result is None:
        raise HTTPException(status_code=404, detail=f"No chain snapshot found for symbol '{payload.symbol.upper()}'")
    return result
