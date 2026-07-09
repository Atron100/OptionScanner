from fastapi.testclient import TestClient

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
