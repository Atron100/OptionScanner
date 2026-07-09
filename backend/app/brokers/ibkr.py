import socket

from app.brokers.base import BrokerStatus, MarketDataBroker, OptionChainData
from app.core.settings import Settings


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
                    "IBKR TCP endpoint is reachable. Live option chain fetching is the next step; "
                    "the current Phase 2 scaffold only verifies connectivity."
                ),
                host=self._settings.ibkr_host,
                port=self._settings.ibkr_port,
                read_only=self._settings.ibkr_read_only,
                supports_live_data=False,
                supports_option_chain_fetch=False,
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
        raise NotImplementedError(
            "Live IBKR option chain fetching is not implemented yet. This Phase 2 scaffold validates "
            "connectivity only. Set OPTIONSCANNER_MARKET_DATA_PROVIDER=mock for local ingestion tests."
        )

    def _probe_socket(self, host: str, port: int) -> tuple[bool, str]:
        try:
            with socket.create_connection((host, port), timeout=1.5):
                return True, ""
        except OSError as exc:
            return False, (
                f"Unable to connect to {host}:{port}. "
                "Make sure TWS or IB Gateway is running locally and API connections are enabled. "
                f"Socket error: {exc}"
            )
