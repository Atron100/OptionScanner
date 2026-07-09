from app.brokers.base import MarketDataBroker
from app.brokers.ibkr import IBKRConnectionManager
from app.brokers.mock import MockMarketDataBroker
from app.core.settings import get_settings


def get_market_data_broker() -> MarketDataBroker:
    settings = get_settings()
    if settings.market_data_provider.lower() == "ibkr":
        return IBKRConnectionManager(settings)
    return MockMarketDataBroker()


def get_ibkr_connection_manager() -> IBKRConnectionManager:
    settings = get_settings()
    return IBKRConnectionManager(settings)
