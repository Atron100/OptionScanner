from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.strategies import GenerateCashSecuredPutRequest, StrategyCandidatesResponse
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
