from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_system_info_endpoint() -> None:
    response = client.get("/api/v1/system/info")
    assert response.status_code == 200
    payload = response.json()
    assert payload["app_name"] == "OptionScanner API"
    assert payload["environment"] == "development"
    assert payload["database_url"].startswith("sqlite:///")
    assert isinstance(payload["database_exists"], bool)
