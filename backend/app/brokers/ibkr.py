from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from app.brokers.base import (
    BrokerStatus,
    MarketDataBroker,
    MarketDataConfigurationError,
    MarketDataUnavailableError,
    OptionChainData,
    OptionQuoteData,
)
from app.core.settings import Settings

try:
    from ibapi.client import EClient
    from ibapi.contract import Contract
    from ibapi.wrapper import EWrapper
except ImportError:  # pragma: no cover - exercised through runtime config path
    EClient = None
    Contract = None
    EWrapper = object


@dataclass(slots=True)
class _UnderlyingContract:
    con_id: int
    symbol: str
    long_name: str | None
    exchange: str | None
    currency: str


class _IBKRDiscoverySession(EWrapper):
    def __init__(self, settings: Settings) -> None:
        if EClient is None or Contract is None:
            raise MarketDataConfigurationError(
                "The official IBKR Python client is not installed. Run backend dependency installation again to add ibapi."
            )

        super().__init__()
        self._settings = settings
        self.client = EClient(self)
        self._thread: threading.Thread | None = None
        self._next_order_id_event = threading.Event()
        self._response_event = threading.Event()
        self._error_message: str | None = None
        self._underlying: _UnderlyingContract | None = None
        self._chain_params: dict[str, Any] | None = None
        self._contract_details: list[Any] = []
        self._pending_contract_request_ids: set[int] = set()
        self._request_mode: str | None = None

    def connect_and_start(self) -> None:
        self.client.connect(
            self._settings.ibkr_host,
            self._settings.ibkr_port,
            self._settings.ibkr_client_id,
        )
        # ibapi's EClient.connect() reports success through connection state,
        # not a return value (it returns None in supported client versions).
        if not self.client.isConnected():
            raise MarketDataUnavailableError(
                f"Unable to open an IBKR API session to {self._settings.ibkr_host}:{self._settings.ibkr_port}."
            )
        self._thread = threading.Thread(target=self.client.run, daemon=True)
        self._thread.start()
        if not self._next_order_id_event.wait(timeout=5):
            self.client.disconnect()
            raise MarketDataUnavailableError(
                "IBKR API session opened but no initialization callback arrived. Check TWS API settings and client ID."
            )

    def shutdown(self) -> None:
        try:
            if self.client.isConnected():
                self.client.disconnect()
        finally:
            if self._thread and self._thread.is_alive():
                self._thread.join(timeout=1)

    def reqId(self, reqId: int) -> None:  # pragma: no cover - signature compatibility helper
        return None

    def nextValidId(self, orderId: int) -> None:  # noqa: N802
        self._next_order_id_event.set()

    def error(self, reqId: int, errorCode: int, errorString: str, advancedOrderRejectJson: str = "") -> None:  # noqa: N802
        benign_codes = {2104, 2106, 2158}
        if errorCode in benign_codes:
            return
        self._error_message = f"IBKR error {errorCode}: {errorString}"
        self._response_event.set()

    def contractDetails(self, reqId: int, contractDetails: Any) -> None:  # noqa: N802
        if self._request_mode == "underlying" and self._underlying is None:
            contract = contractDetails.contract
            self._underlying = _UnderlyingContract(
                con_id=contract.conId,
                symbol=contract.symbol,
                long_name=getattr(contractDetails, "longName", None),
                exchange=contract.primaryExchange or contract.exchange,
                currency=contract.currency,
            )
        elif self._request_mode == "options":
            self._contract_details.append(contractDetails)

    def contractDetailsEnd(self, reqId: int) -> None:  # noqa: N802
        if self._request_mode == "options":
            self._pending_contract_request_ids.discard(reqId)
            if self._pending_contract_request_ids:
                return
        self._response_event.set()

    def securityDefinitionOptionParameter(  # noqa: N802
        self,
        reqId: int,
        exchange: str,
        underlyingConId: int,
        tradingClass: str,
        multiplier: str,
        expirations: set[str],
        strikes: set[float],
    ) -> None:
        preferred_exchange = self._settings.ibkr_exchange.upper()
        if exchange.upper() == preferred_exchange or self._chain_params is None:
            self._chain_params = {
                "exchange": exchange,
                "underlying_con_id": underlyingConId,
                "trading_class": tradingClass,
                "multiplier": multiplier,
                "expirations": expirations,
                "strikes": strikes,
            }

    def securityDefinitionOptionParameterEnd(self, reqId: int) -> None:  # noqa: N802
        self._response_event.set()

    def discover_option_chain(self, symbol: str) -> OptionChainData:
        underlying = self._resolve_underlying(symbol)
        chain_params = self._resolve_chain_parameters(symbol, underlying)
        option_contracts = self._resolve_option_contracts(symbol, chain_params)

        if not option_contracts:
            raise MarketDataUnavailableError(
                f"IBKR returned no option contracts for {symbol.upper()} using the current bounded discovery settings."
            )

        quotes = [
            OptionQuoteData(
                expiration_date=datetime.strptime(details.contract.lastTradeDateOrContractMonth, "%Y%m%d").date(),
                right=details.contract.right,
                strike=float(details.contract.strike),
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
                multiplier=int(details.contract.multiplier or chain_params["multiplier"] or 100),
                ib_contract_id=details.contract.conId,
            )
            for details in option_contracts
        ]

        return OptionChainData(
            provider="ibkr",
            symbol=underlying.symbol.upper(),
            name=underlying.long_name,
            exchange=underlying.exchange,
            currency=underlying.currency,
            as_of=datetime.now(timezone.utc).replace(microsecond=0),
            quotes=quotes,
        )

    def _resolve_underlying(self, symbol: str) -> _UnderlyingContract:
        self._request_mode = "underlying"
        self._underlying = None
        self._error_message = None
        self._response_event.clear()

        contract = Contract()
        contract.symbol = symbol.upper()
        contract.secType = "STK"
        contract.exchange = self._settings.ibkr_exchange
        contract.currency = self._settings.ibkr_currency

        self.client.reqContractDetails(1001, contract)
        self._wait_for_response("underlying contract lookup")
        if self._underlying is None:
            raise MarketDataUnavailableError(f"IBKR returned no stock contract details for symbol '{symbol.upper()}'.")
        return self._underlying

    def _resolve_chain_parameters(self, symbol: str, underlying: _UnderlyingContract) -> dict[str, Any]:
        self._request_mode = "chain-params"
        self._chain_params = None
        self._error_message = None
        self._response_event.clear()

        self.client.reqSecDefOptParams(1002, symbol.upper(), "", "STK", underlying.con_id)
        self._wait_for_response("option chain discovery")

        if self._chain_params is None:
            raise MarketDataUnavailableError(
                f"IBKR returned no option chain parameters for symbol '{symbol.upper()}'."
            )
        return self._chain_params

    def _resolve_option_contracts(self, symbol: str, chain_params: dict[str, Any]) -> list[Any]:
        expirations = sorted(chain_params["expirations"])[: self._settings.ibkr_max_expirations]
        if not expirations:
            raise MarketDataUnavailableError(f"IBKR returned no expirations for symbol '{symbol.upper()}'.")

        strikes = sorted(float(strike) for strike in chain_params["strikes"])
        if not strikes:
            raise MarketDataUnavailableError(f"IBKR returned no strikes for symbol '{symbol.upper()}'.")

        middle_index = len(strikes) // 2
        width = max(self._settings.ibkr_strikes_per_side, 1)
        selected_strikes = strikes[max(0, middle_index - width) : middle_index + width]

        self._request_mode = "options"
        self._contract_details = []
        self._error_message = None
        self._response_event.clear()

        requests: list[tuple[int, Any]] = []
        request_id = 2000
        for expiration in expirations:
            for right in ("C", "P"):
                for strike in selected_strikes:
                    contract = Contract()
                    contract.symbol = symbol.upper()
                    contract.secType = "OPT"
                    contract.exchange = chain_params["exchange"]
                    contract.currency = self._settings.ibkr_currency
                    contract.lastTradeDateOrContractMonth = expiration
                    contract.strike = strike
                    contract.right = right
                    contract.multiplier = str(chain_params["multiplier"] or 100)
                    contract.tradingClass = chain_params["trading_class"]
                    requests.append((request_id, contract))
                    request_id += 1

        # IBKR sends one contractDetailsEnd callback per request. Register the
        # entire batch first so an early callback cannot end discovery early.
        self._pending_contract_request_ids = {request_id for request_id, _ in requests}
        for request_id, contract in requests:
            self.client.reqContractDetails(request_id, contract)

        self._wait_for_response("option contract details", timeout=12)
        deduped: dict[int, Any] = {}
        for details in self._contract_details:
            deduped[details.contract.conId] = details
        return list(deduped.values())

    def _wait_for_response(self, operation: str, timeout: int = 8) -> None:
        if not self._response_event.wait(timeout=timeout):
            raise MarketDataUnavailableError(f"Timed out waiting for IBKR {operation}.")
        if self._error_message:
            raise MarketDataUnavailableError(self._error_message)


class IBKRConnectionManager(MarketDataBroker):
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def get_connection_status(self) -> BrokerStatus:
        configured = bool(self._settings.ibkr_host.strip()) and self._settings.ibkr_port > 0
        if not configured:
            return BrokerStatus(
                provider="ibkr",
                configured=False,
                connected=False,
                message="IBKR host or port is missing from configuration.",
                host=self._settings.ibkr_host,
                port=self._settings.ibkr_port,
                read_only=self._settings.ibkr_read_only,
            )

        connected, error_message = self._probe_socket(self._settings.ibkr_host, self._settings.ibkr_port)
        if connected:
            return BrokerStatus(
                provider="ibkr",
                configured=True,
                connected=True,
                message=(
                    "IBKR TCP endpoint is reachable. Live bounded option chain discovery is enabled; "
                    "quote enrichment is still pending."
                ),
                host=self._settings.ibkr_host,
                port=self._settings.ibkr_port,
                read_only=self._settings.ibkr_read_only,
                supports_live_data=False,
                supports_option_chain_fetch=True,
            )

        return BrokerStatus(
            provider="ibkr",
            configured=True,
            connected=False,
            message=(
                "IBKR configuration is present, but the TCP endpoint is not reachable. "
                f"{error_message}"
            ),
            host=self._settings.ibkr_host,
            port=self._settings.ibkr_port,
            read_only=self._settings.ibkr_read_only,
        )

    def fetch_option_chain(self, symbol: str) -> OptionChainData:
        session = _IBKRDiscoverySession(self._settings)
        session.connect_and_start()
        try:
            return session.discover_option_chain(symbol)
        finally:
            session.shutdown()

    def _probe_socket(self, host: str, port: int) -> tuple[bool, str]:
        import socket

        try:
            with socket.create_connection((host, port), timeout=1.5):
                return True, ""
        except OSError as exc:
            return False, (
                f"Unable to connect to {host}:{port}. "
                "Make sure TWS or IB Gateway is running locally and API connections are enabled. "
                f"Socket error: {exc}"
            )
