from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_market_data_broker
from app.brokers.base import MarketDataBroker
from app.db.session import get_db
from app.schemas.market_data import (
    ChainSnapshotResponse,
    IngestChainRequest,
    IngestChainResponse,
)
from app.services.market_data import MarketDataIngestionService, MarketDataQueryService

router = APIRouter(prefix="/market-data")


@router.post("/ingest", response_model=IngestChainResponse)
def ingest_chain(
    payload: IngestChainRequest,
    db: Session = Depends(get_db),
    broker: MarketDataBroker = Depends(get_market_data_broker),
) -> IngestChainResponse:
    service = MarketDataIngestionService(db, broker)
    result = service.ingest_symbol(payload.symbol)
    return IngestChainResponse.model_validate(result)


@router.get("/underlyings/{symbol}/latest-chain", response_model=ChainSnapshotResponse)
def latest_chain(symbol: str, db: Session = Depends(get_db)) -> ChainSnapshotResponse:
    service = MarketDataQueryService(db)
    result = service.get_latest_chain(symbol)
    if result is None:
        raise HTTPException(status_code=404, detail=f"No chain snapshot found for symbol '{symbol.upper()}'")
    return ChainSnapshotResponse.model_validate(result)
