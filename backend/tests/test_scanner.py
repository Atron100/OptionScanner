from datetime import date

from fastapi.testclient import TestClient

from app.api.dependencies import get_market_data_broker
from app.brokers.mock import MockMarketDataBroker
from app.main import app


client = TestClient(app)


def _ingest(symbol: str) -> None:
    response = client.post("/api/v1/market-data/ingest", json={"symbol": symbol})
    assert response.status_code == 200


def test_scanner_ranks_candidates_deterministically_and_calculates_expected_value() -> None:
    _ingest("AAPL")
    _ingest("SPY")

    response = client.post(
        "/api/v1/scanner/scan",
        json={
            "symbols": ["spy", "AAPL", "spy"],
            "strategies": ["cash_secured_put", "cash_secured_put"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["symbols"] == ["SPY", "AAPL"]
    assert payload["strategies"] == ["cash_secured_put"]
    assert payload["total_candidates"] == 4
    assert payload["eligible_candidate_count"] == 4
    assert payload["filtered_out_count"] == 0
    assert payload["result_count"] == 4
    assert [result["rank"] for result in payload["results"]] == [1, 2, 3, 4]
    scores = [result["candidate"]["score"] for result in payload["results"]]
    assert scores == sorted(scores, reverse=True)

    first = payload["results"][0]
    candidate = first["candidate"]
    expected_value = round(
        candidate["probability_of_profit"] * candidate["max_profit"]
        - (1 - candidate["probability_of_profit"]) * candidate["max_loss"],
        6,
    )
    assert first["expected_value"] == expected_value


def test_scanner_applies_risk_filter_and_reports_missing_symbols() -> None:
    _ingest("AAPL")
    _ingest("SPY")

    response = client.post(
        "/api/v1/scanner/scan",
        json={
            "symbols": ["AAPL", "SPY", "MISSING"],
            "strategies": ["cash_secured_put"],
            "maximum_loss": 30000,
            "limit": 1,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_candidates"] == 4
    assert payload["eligible_candidate_count"] == 2
    assert payload["filtered_out_count"] == 2
    assert payload["result_count"] == 1
    assert payload["results"][0]["candidate"]["symbol"] == "AAPL"
    assert payload["results"][0]["candidate"]["max_loss"] <= 30000
    assert payload["warnings"] == ["No chain snapshot found for symbol 'MISSING'."]


def test_scanner_rejects_unsupported_strategy() -> None:
    response = client.post(
        "/api/v1/scanner/scan",
        json={"symbols": ["AAPL"], "strategies": ["covered_call"]},
    )

    assert response.status_code == 422


def test_scanner_default_filters_exclude_same_day_contracts() -> None:
    class SameDayBroker(MockMarketDataBroker):
        def fetch_option_chain(self, symbol: str, strike: float | None = None, expiration_count: int | None = None):
            chain = super().fetch_option_chain(symbol, strike, expiration_count)
            for quote in chain.quotes:
                quote.expiration_date = date.today()
            return chain

    app.dependency_overrides[get_market_data_broker] = SameDayBroker
    try:
        _ingest("DAY")
    finally:
        app.dependency_overrides.pop(get_market_data_broker, None)

    response = client.post(
        "/api/v1/scanner/scan",
        json={"symbols": ["DAY"], "strategies": ["cash_secured_put"]},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_candidates"] == 1
    assert payload["eligible_candidate_count"] == 0
    assert payload["filtered_out_count"] == 1
    assert payload["result_count"] == 0


def test_scanner_applies_credit_and_liquidity_thresholds() -> None:
    _ingest("AAPL")

    response = client.post(
        "/api/v1/scanner/scan",
        json={
            "symbols": ["AAPL"],
            "strategies": ["cash_secured_put"],
            "minimum_credit": 4.5,
            "minimum_open_interest": 700,
            "minimum_volume": 200,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_candidates"] == 2
    assert payload["eligible_candidate_count"] == 1
    assert payload["results"][0]["candidate"]["strike"] == 200


def test_scanner_rejects_inverted_expiration_range() -> None:
    response = client.post(
        "/api/v1/scanner/scan",
        json={
            "symbols": ["AAPL"],
            "minimum_days_to_expiration": 30,
            "maximum_days_to_expiration": 10,
        },
    )

    assert response.status_code == 422


def test_scanner_persists_and_restores_recent_history() -> None:
    _ingest("AAPL")
    first = client.post(
        "/api/v1/scanner/scan",
        json={"symbols": ["AAPL"], "strategies": ["cash_secured_put"], "limit": 1},
    )
    second = client.post(
        "/api/v1/scanner/scan",
        json={"symbols": ["AAPL"], "strategies": ["iron_condor"], "limit": 2},
    )

    history = client.get("/api/v1/scanner/history?limit=1")

    assert first.status_code == second.status_code == history.status_code == 200
    history_payload = history.json()
    assert history_payload["count"] == 1
    assert history_payload["runs"][0]["strategies"] == ["iron_condor"]
    assert history_payload["runs"][0]["result_count"] == second.json()["result_count"]

    run_id = history_payload["runs"][0]["id"]
    detail = client.get(f"/api/v1/scanner/history/{run_id}")
    assert detail.status_code == 200
    assert detail.json()["request"]["limit"] == 2
    assert detail.json()["response"] == second.json()


def test_scan_history_returns_not_found_for_unknown_run() -> None:
    response = client.get("/api/v1/scanner/history/999")

    assert response.status_code == 404
