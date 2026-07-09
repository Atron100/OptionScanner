from dataclasses import asdict

from fastapi import APIRouter, Depends

from app.api.dependencies import get_ibkr_connection_manager, get_market_data_broker
from app.brokers.base import MarketDataBroker
from app.brokers.ibkr import IBKRConnectionManager
from app.schemas.brokers import BrokerStatusResponse

router = APIRouter(prefix="/brokers")


@router.get("/market-data/status", response_model=BrokerStatusResponse)
def market_data_status(broker: MarketDataBroker = Depends(get_market_data_broker)) -> BrokerStatusResponse:
    status = broker.get_connection_status()
    return BrokerStatusResponse.model_validate(asdict(status))


@router.get("/ibkr/status", response_model=BrokerStatusResponse)
def ibkr_status(broker: IBKRConnectionManager = Depends(get_ibkr_connection_manager)) -> BrokerStatusResponse:
    status = broker.get_connection_status()
    return BrokerStatusResponse.model_validate(asdict(status))
