from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_market_data_broker
from app.brokers.base import (
    MarketDataBroker,
    MarketDataBrokerError,
    MarketDataConfigurationError,
    MarketDataUnavailableError,
)
from app.db.session import get_db
from app.schemas.market_data import (
    ChainSnapshotResponse,
    IngestChainRequest,
    IngestChainResponse,
    HistoricalBarsResponse,
    IngestHistoricalBarsRequest,
)
from app.services.market_data import HistoricalOptionDataService, MarketDataIngestionService, MarketDataQueryService

router = APIRouter(prefix="/market-data")


@router.post("/ingest", response_model=IngestChainResponse)
def ingest_chain(
    payload: IngestChainRequest,
    db: Session = Depends(get_db),
    broker: MarketDataBroker = Depends(get_market_data_broker),
) -> IngestChainResponse:
    service = MarketDataIngestionService(db, broker)
    try:
        result = service.ingest_symbol(payload.symbol, payload.strike, payload.expiration_count)
    except MarketDataConfigurationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except MarketDataUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except MarketDataBrokerError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return IngestChainResponse.model_validate(result)


@router.get("/underlyings/{symbol}/latest-chain", response_model=ChainSnapshotResponse)
def latest_chain(symbol: str, db: Session = Depends(get_db)) -> ChainSnapshotResponse:
    service = MarketDataQueryService(db)
    result = service.get_latest_chain(symbol)
    if result is None:
        raise HTTPException(status_code=404, detail=f"No chain snapshot found for symbol '{symbol.upper()}'")
    return ChainSnapshotResponse.model_validate(result)


@router.post("/historical/ingest", response_model=HistoricalBarsResponse)
def ingest_historical_bars(
    payload: IngestHistoricalBarsRequest,
    db: Session = Depends(get_db),
    broker: MarketDataBroker = Depends(get_market_data_broker),
) -> HistoricalBarsResponse:
    service = HistoricalOptionDataService(db, broker)
    try:
        result = service.ingest_history(
            payload.symbol,
            payload.expiration_date,
            payload.right,
            payload.strike,
            payload.duration_months,
        )
    except MarketDataConfigurationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except MarketDataUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except MarketDataBrokerError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return HistoricalBarsResponse.model_validate(result)
