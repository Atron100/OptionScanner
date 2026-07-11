from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any

from app.brokers.base import (
    BrokerStatus,
    HistoricalBarData,
    MarketDataBroker,
    MarketDataConfigurationError,
    MarketDataUnavailableError,
    OptionChainData,
    OptionContractReference,
    OptionHistoryData,
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
        self._option_quotes: dict[int, OptionQuoteData] = {}
        self._pending_quote_request_ids: set[int] = set()
        self._quote_warnings: list[str] = []
        self._discovery_warnings: list[str] = []
        self._historical_bars: list[HistoricalBarData] = []
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
        if self._request_mode == "options" and reqId in self._pending_contract_request_ids:
            # Chain parameters may list strikes that do not resolve for every
            # expiration. Keep the remaining valid contract definitions.
            warning = f"IBKR error {errorCode}: {errorString}"
            if warning not in self._discovery_warnings:
                self._discovery_warnings.append(warning)
            self._pending_contract_request_ids.discard(reqId)
            if not self._pending_contract_request_ids:
                self._response_event.set()
            return
        if self._request_mode == "quotes" and reqId in self._pending_quote_request_ids:
            # A missing live-data subscription must not discard otherwise valid
            # contract definitions. The affected quote remains empty.
            warning = f"IBKR error {errorCode}: {errorString}"
            if warning not in self._quote_warnings:
                self._quote_warnings.append(warning)
            self._pending_quote_request_ids.discard(reqId)
            self._complete_quote_batch_if_ready()
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

    def tickPrice(self, reqId: int, tickType: int, price: float, attrib: Any) -> None:  # noqa: N802
        quote = self._option_quotes.get(reqId)
        if quote is None:
            return
        value = self._normalise_non_negative_number(price)
        if tickType == 1:
            quote.bid = value
        elif tickType == 2:
            quote.ask = value
        elif tickType == 4:
            quote.last = value
        elif tickType == 37:
            quote.mark = value

    def tickSize(self, reqId: int, tickType: int, size: float) -> None:  # noqa: N802
        quote = self._option_quotes.get(reqId)
        if quote is None:
            return
        value = self._normalise_non_negative_integer(size)
        if tickType in {8, 29, 30}:
            quote.volume = value
        elif tickType in {22, 27, 28}:
            quote.open_interest = value

    def tickGeneric(self, reqId: int, tickType: int, value: float) -> None:  # noqa: N802
        quote = self._option_quotes.get(reqId)
        if quote is not None and tickType == 24:
            quote.implied_volatility = self._normalise_non_negative_number(value)

    def tickOptionComputation(  # noqa: N802
        self,
        reqId: int,
        tickType: int,
        tickAttrib: int,
        impliedVol: float,
        delta: float,
        optPrice: float,
        pvDividend: float,
        gamma: float,
        vega: float,
        theta: float,
        undPrice: float,
    ) -> None:
        quote = self._option_quotes.get(reqId)
        if quote is None or tickType not in {10, 11, 12, 13}:
            return
        quote.implied_volatility = self._normalise_non_negative_number(impliedVol)
        quote.delta = self._normalise_number(delta)
        quote.gamma = self._normalise_number(gamma)
        quote.theta = self._normalise_number(theta)
        quote.vega = self._normalise_number(vega)
        option_price = self._normalise_number(optPrice)
        if quote.mark is None and option_price is not None:
            quote.mark = option_price

    def tickSnapshotEnd(self, reqId: int) -> None:  # noqa: N802
        self._pending_quote_request_ids.discard(reqId)
        self._complete_quote_batch_if_ready()

    def historicalData(self, reqId: int, bar: Any) -> None:  # noqa: N802
        if self._request_mode != "history":
            return
        bar_date = datetime.strptime(str(bar.date)[:8], "%Y%m%d").date()
        volume = int(float(bar.volume)) if bar.volume is not None else None
        if self._historical_bars and self._historical_bars[-1].bar_date == bar_date:
            daily_bar = self._historical_bars[-1]
            daily_bar.high = max(daily_bar.high, float(bar.high))
            daily_bar.low = min(daily_bar.low, float(bar.low))
            daily_bar.close = float(bar.close)
            if volume is not None:
                daily_bar.volume = (daily_bar.volume or 0) + volume
            return
        self._historical_bars.append(
            HistoricalBarData(
                bar_date=bar_date,
                open=float(bar.open),
                high=float(bar.high),
                low=float(bar.low),
                close=float(bar.close),
                volume=volume,
            )
        )

    def historicalDataEnd(self, reqId: int, start: str, end: str) -> None:  # noqa: N802
        if self._request_mode == "history":
            self._response_event.set()

    def discover_option_chain(
        self,
        symbol: str,
        strike: float | None = None,
        expiration_count: int | None = None,
    ) -> OptionChainData:
        underlying = self._resolve_underlying(symbol)
        chain_params = self._resolve_chain_parameters(symbol, underlying)
        option_contracts = self._resolve_option_contracts(symbol, chain_params, strike, expiration_count)

        if not option_contracts:
            raise MarketDataUnavailableError(
                f"IBKR returned no option contracts for {symbol.upper()} using the current bounded discovery settings."
            )

        quotes = self._fetch_option_quotes(option_contracts, chain_params)

        return OptionChainData(
            provider="ibkr",
            symbol=underlying.symbol.upper(),
            name=underlying.long_name,
            exchange=underlying.exchange,
            currency=underlying.currency,
            as_of=datetime.now(timezone.utc).replace(microsecond=0),
            quotes=quotes,
            warnings=self._discovery_warnings + self._quote_warnings,
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

    def fetch_option_history(self, contract_reference: OptionContractReference, duration_months: int) -> OptionHistoryData:
        self._request_mode = "history"
        self._historical_bars = []
        self._error_message = None
        self._response_event.clear()

        contract = Contract()
        contract.conId = contract_reference.ib_contract_id or 0
        contract.symbol = contract_reference.symbol
        contract.secType = "OPT"
        contract.exchange = contract_reference.exchange
        contract.currency = contract_reference.currency
        contract.lastTradeDateOrContractMonth = contract_reference.expiration_date.strftime("%Y%m%d")
        contract.strike = contract_reference.strike
        contract.right = contract_reference.right
        contract.multiplier = str(contract_reference.multiplier)
        contract.tradingClass = contract_reference.symbol
        contract.localSymbol = self._occ_local_symbol(contract_reference)

        self.client.reqHistoricalData(
            4000,
            contract,
            "",
            f"{duration_months} M",
            "1 hour",
            "TRADES",
            1,
            1,
            False,
            [],
        )
        self._wait_for_response("historical option bars", timeout=20)
        return OptionHistoryData(provider="ibkr", bars=self._historical_bars)

    @staticmethod
    def _occ_local_symbol(contract: OptionContractReference) -> str:
        expiration = contract.expiration_date.strftime("%y%m%d")
        strike = int(round(contract.strike * 1000))
        return f"{contract.symbol:<6}{expiration}{contract.right}{strike:08d}"

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

    def _resolve_option_contracts(
        self,
        symbol: str,
        chain_params: dict[str, Any],
        strike: float | None = None,
        expiration_count: int | None = None,
    ) -> list[Any]:
        expirations = self._select_expirations(chain_params["expirations"], expiration_count)
        if not expirations:
            raise MarketDataUnavailableError(f"IBKR returned no expirations for symbol '{symbol.upper()}'.")

        strikes = sorted(float(strike) for strike in chain_params["strikes"])
        if not strikes:
            raise MarketDataUnavailableError(f"IBKR returned no strikes for symbol '{symbol.upper()}'.")

        if strike is not None:
            if strike not in strikes:
                raise MarketDataUnavailableError(
                    f"IBKR returned no option contracts for strike {strike:g} on symbol '{symbol.upper()}'."
                )
            selected_strikes = [strike]
        else:
            middle_index = len(strikes) // 2
            width = max(self._settings.ibkr_strikes_per_side, 1)
            selected_strikes = strikes[max(0, middle_index - width) : middle_index + width]

        self._request_mode = "options"
        self._contract_details = []
        self._discovery_warnings = []
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
        self._send_paced_requests(requests, self.client.reqContractDetails)

        self._wait_for_response("option contract details", timeout=self._batch_timeout(len(requests)))
        deduped: dict[int, Any] = {}
        for details in self._contract_details:
            deduped[details.contract.conId] = details
        return list(deduped.values())

    def _fetch_option_quotes(self, option_contracts: list[Any], chain_params: dict[str, Any]) -> list[OptionQuoteData]:
        self._request_mode = "quotes"
        self._error_message = None
        self._response_event.clear()
        self._option_quotes = {}
        self._quote_warnings = []

        requests: list[tuple[int, Any]] = []
        for offset, details in enumerate(option_contracts):
            request_id = 3000 + offset
            contract = details.contract
            self._option_quotes[request_id] = OptionQuoteData(
                expiration_date=datetime.strptime(contract.lastTradeDateOrContractMonth, "%Y%m%d").date(),
                right=contract.right,
                strike=float(contract.strike),
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
                multiplier=int(contract.multiplier or chain_params["multiplier"] or 100),
                ib_contract_id=contract.conId,
            )
            requests.append((request_id, contract))

        self._pending_quote_request_ids = {request_id for request_id, _ in requests}
        self._send_paced_requests(
            requests,
            lambda request_id, contract: self.client.reqMktData(request_id, contract, "100,101", False, False, []),
        )

        # Collect a bounded burst of updates, then immediately release all
        # streaming subscriptions to stay within IBKR market-data limits.
        threading.Event().wait(timeout=self._settings.ibkr_quote_collection_seconds)
        for request_id, _ in requests:
            self.client.cancelMktData(request_id)
        for quote in self._option_quotes.values():
            if quote.mark is None and quote.bid is not None and quote.ask is not None:
                quote.mark = round((quote.bid + quote.ask) / 2, 6)
        return list(self._option_quotes.values())

    def _complete_quote_batch_if_ready(self) -> None:
        if not self._pending_quote_request_ids:
            self._response_event.set()

    def _select_expirations(
        self,
        available_expirations: set[str],
        expiration_count: int | None = None,
        today: date | None = None,
    ) -> list[str]:
        today = today or datetime.now(timezone.utc).date()
        latest_date = today + timedelta(days=self._settings.ibkr_expiration_horizon_days)
        selected = [
            expiration
            for expiration in sorted(available_expirations)
            if today <= datetime.strptime(expiration, "%Y%m%d").date() <= latest_date
        ]
        limit = expiration_count if expiration_count is not None else self._settings.ibkr_max_expirations
        if limit > 0:
            return selected[:limit]
        return selected

    def _send_paced_requests(self, requests: list[tuple[int, Any]], sender: Any) -> None:
        interval = 1 / max(self._settings.ibkr_max_requests_per_second, 1)
        for index, (request_id, contract) in enumerate(requests):
            sender(request_id, contract)
            if index < len(requests) - 1:
                threading.Event().wait(timeout=interval)

    def _batch_timeout(self, request_count: int) -> float:
        request_duration = request_count / max(self._settings.ibkr_max_requests_per_second, 1)
        return max(12.0, request_duration + 10.0)

    @staticmethod
    def _normalise_number(value: float) -> float | None:
        if value is None or abs(value) > 1e100:
            return None
        return float(value)

    @classmethod
    def _normalise_non_negative_number(cls, value: float) -> float | None:
        normalised = cls._normalise_number(value)
        if normalised is None or normalised < 0:
            return None
        return normalised

    @classmethod
    def _normalise_non_negative_integer(cls, value: float) -> int | None:
        normalised = cls._normalise_non_negative_number(value)
        return int(normalised) if normalised is not None else None

    def _wait_for_response(self, operation: str, timeout: float = 8) -> None:
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
                    "IBKR TCP endpoint is reachable. Live bounded option chain and quote fetching are enabled."
                ),
                host=self._settings.ibkr_host,
                port=self._settings.ibkr_port,
                read_only=self._settings.ibkr_read_only,
                supports_live_data=True,
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

    def fetch_option_chain(
        self,
        symbol: str,
        strike: float | None = None,
        expiration_count: int | None = None,
    ) -> OptionChainData:
        session = _IBKRDiscoverySession(self._settings)
        session.connect_and_start()
        try:
            return session.discover_option_chain(symbol, strike, expiration_count)
        finally:
            session.shutdown()

    def fetch_option_history(self, contract: OptionContractReference, duration_months: int) -> OptionHistoryData:
        session = _IBKRDiscoverySession(self._settings)
        session.connect_and_start()
        try:
            return session.fetch_option_history(contract, duration_months)
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
