import pytest

from app.api.dependencies import get_market_data_broker
from app.brokers.mock import MockMarketDataBroker
from app.db.base import Base
from app.db.session import engine
from app.main import app


@pytest.fixture(autouse=True)
def reset_database() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture(autouse=True)
def use_mock_market_data_broker() -> None:
    """Keep automated tests independent of a developer's live broker settings."""
    app.dependency_overrides[get_market_data_broker] = MockMarketDataBroker
    yield
    app.dependency_overrides.pop(get_market_data_broker, None)
