import threading
from datetime import date

from fastapi.testclient import TestClient

from app.brokers.base import OptionContractReference, OptionQuoteData
from app.brokers.ibkr import IBKRConnectionManager, _IBKRDiscoverySession
from app.main import app


client = TestClient(app)


def test_ibkr_contract_batch_waits_for_all_request_completion_callbacks() -> None:
    session = object.__new__(_IBKRDiscoverySession)
    session._request_mode = "options"
    session._pending_contract_request_ids = {2000, 2001}
    session._response_event = threading.Event()

    session.contractDetailsEnd(2000)
    assert session._pending_contract_request_ids == {2001}
    assert not session._response_event.is_set()

    session.contractDetailsEnd(2001)
    assert session._pending_contract_request_ids == set()
    assert session._response_event.is_set()


def test_ibkr_selects_all_expirations_within_configured_horizon() -> None:
    session = object.__new__(_IBKRDiscoverySession)
    session._settings = type(
        "SettingsStub",
        (),
        {"ibkr_expiration_horizon_days": 21, "ibkr_max_expirations": 0},
    )()

    selected = session._select_expirations(
        {"20260710", "20260713", "20260717", "20260724", "20260731", "20260807"},
        today=date(2026, 7, 10),
    )

    assert selected == ["20260710", "20260713", "20260717", "20260724", "20260731"]


def test_ibkr_contract_lookup_error_keeps_other_batch_requests_running() -> None:
    session = object.__new__(_IBKRDiscoverySession)
    session._request_mode = "options"
    session._pending_contract_request_ids = {2000, 2001}
    session._discovery_warnings = []
    session._response_event = threading.Event()

    session.error(2000, 200, "No security definition has been found for the request")

    assert session._pending_contract_request_ids == {2001}
    assert session._discovery_warnings == ["IBKR error 200: No security definition has been found for the request"]
    assert not session._response_event.is_set()


def test_ibkr_builds_occ_local_symbol_for_historical_option_request() -> None:
    contract = OptionContractReference(
        symbol="AAPL",
        expiration_date=date(2026, 7, 20),
        right="C",
        strike=315,
        multiplier=100,
        ib_contract_id=898626100,
    )

    assert _IBKRDiscoverySession._occ_local_symbol(contract) == "AAPL  260720C00315000"


def test_ibkr_quote_callbacks_collect_values_and_wait_for_all_requests() -> None:
    session = object.__new__(_IBKRDiscoverySession)
    session._request_mode = "quotes"
    session._response_event = threading.Event()
    session._pending_quote_request_ids = {3000, 3001}
    session._option_quotes = {
        3000: OptionQuoteData(
            expiration_date=date(2026, 7, 10),
            right="C",
            strike=280.0,
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
        )
    }

    session.tickPrice(3000, 1, 4.2, None)
    session.tickPrice(3000, 2, 4.4, None)
    session.tickPrice(3000, 37, 4.3, None)
    session.tickSize(3000, 29, 120)
    session.tickSize(3000, 27, 900)
    session.tickOptionComputation(3000, 13, 0, 0.25, 0.5, 4.3, 0, 0.02, 0.1, -0.04, 280)
    session.tickSnapshotEnd(3000)

    quote = session._option_quotes[3000]
    assert quote.bid == 4.2
    assert quote.ask == 4.4
    assert quote.mark == 4.3
    assert quote.volume == 120
    assert quote.open_interest == 900
    assert quote.implied_volatility == 0.25
    assert quote.delta == 0.5
    assert quote.gamma == 0.02
    assert quote.theta == -0.04
    assert quote.vega == 0.1
    assert not session._response_event.is_set()

    session.tickSnapshotEnd(3001)
    assert session._response_event.is_set()


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
