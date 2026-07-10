from fastapi.testclient import TestClient

from app.api.dependencies import get_market_data_broker
from app.brokers.base import MarketDataBroker
from app.brokers.mock import MockMarketDataBroker
from app.main import app


client = TestClient(app)


def test_ingest_chain_persists_and_returns_latest_snapshot() -> None:
    ingest_response = client.post("/api/v1/market-data/ingest", json={"symbol": "AAPL"})

    assert ingest_response.status_code == 200
    ingest_payload = ingest_response.json()
    assert ingest_payload["symbol"] == "AAPL"
    assert ingest_payload["provider"] == "mock"
    assert ingest_payload["quote_count"] == 4
    assert ingest_payload["contract_count"] == 4
    assert ingest_payload["expirations"] == ["2026-08-21", "2026-09-18"]

    latest_response = client.get("/api/v1/market-data/underlyings/AAPL/latest-chain")
    assert latest_response.status_code == 200

    latest_payload = latest_response.json()
    assert latest_payload["symbol"] == "AAPL"
    assert latest_payload["provider"] == "mock"
    assert latest_payload["quote_count"] == 4
    assert len(latest_payload["contracts"]) == 4
    assert latest_payload["contracts"][0]["expiration_date"] == "2026-08-21"


def test_reingest_creates_new_snapshot_without_duplicate_contract_definitions() -> None:
    first = client.post("/api/v1/market-data/ingest", json={"symbol": "SPY"})
    second = client.post("/api/v1/market-data/ingest", json={"symbol": "SPY"})

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["snapshot_id"] != second.json()["snapshot_id"]

    latest_response = client.get("/api/v1/market-data/underlyings/SPY/latest-chain")
    latest_payload = latest_response.json()
    assert latest_payload["symbol"] == "SPY"
    assert latest_payload["quote_count"] == 4


def test_ingest_chain_with_live_provider_override_uses_bound_broker_interface() -> None:
    class LiveStyleBroker(MockMarketDataBroker):
        def fetch_option_chain(self, symbol: str):
            chain = super().fetch_option_chain(symbol)
            return chain.__class__(
                provider="ibkr",
                symbol=chain.symbol,
                name=chain.name,
                exchange=chain.exchange,
                currency=chain.currency,
                as_of=chain.as_of,
                quotes=[
                    quote.__class__(
                        expiration_date=quote.expiration_date,
                        right=quote.right,
                        strike=quote.strike,
                        bid=None,
                        ask=None,
                        last=None,
                        mark=None,
                        implied_volatility=None,
                        delta=None,
                        gamma=None,
                        theta=None,
                        vega=None,
                        open_interest=None,
                        volume=None,
                        multiplier=quote.multiplier,
                        ib_contract_id=100000 + index,
                    )
                    for index, quote in enumerate(chain.quotes, start=1)
                ],
            )

    app.dependency_overrides[get_market_data_broker] = lambda: LiveStyleBroker()
    try:
        ingest_response = client.post("/api/v1/market-data/ingest", json={"symbol": "AAPL"})
    finally:
        app.dependency_overrides.pop(get_market_data_broker, None)

    assert ingest_response.status_code == 200
    payload = ingest_response.json()
    assert payload["provider"] == "ibkr"
    assert payload["quote_count"] == 4
