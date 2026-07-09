from fastapi.testclient import TestClient

from app.brokers.ibkr import IBKRConnectionManager
from app.main import app


client = TestClient(app)


def test_broker_status_endpoint_uses_mock_provider() -> None:
    response = client.get("/api/v1/brokers/market-data/status")

    assert response.status_code == 200
    assert response.json() == {
        "provider": "mock",
        "configured": True,
        "connected": True,
        "message": "Mock market data provider ready for local development.",
        "host": None,
        "port": None,
        "read_only": None,
        "supports_live_data": False,
        "supports_option_chain_fetch": True,
    }


def test_ibkr_status_endpoint_reports_unreachable_socket(monkeypatch) -> None:
    def fake_probe_socket(self, host: str, port: int) -> tuple[bool, str]:
        return False, f"Unable to connect to {host}:{port}. Socket error: test"

    monkeypatch.setattr(IBKRConnectionManager, "_probe_socket", fake_probe_socket)

    response = client.get("/api/v1/brokers/ibkr/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["provider"] == "ibkr"
    assert payload["configured"] is True
    assert payload["connected"] is False
    assert payload["host"] == "127.0.0.1"
    assert payload["port"] == 7497
    assert payload["read_only"] is True
    assert payload["supports_live_data"] is False
    assert payload["supports_option_chain_fetch"] is False
    assert "Unable to connect to 127.0.0.1:7497" in payload["message"]
