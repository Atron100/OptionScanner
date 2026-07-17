from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime


@dataclass(slots=True)
class BrokerStatus:
    provider: str
    configured: bool
    connected: bool
    message: str
    host: str | None = None
    port: int | None = None
    read_only: bool | None = None
    supports_live_data: bool = False
    supports_option_chain_fetch: bool = False


@dataclass(slots=True)
class OptionQuoteData:
    expiration_date: date
    right: str
    strike: float
    bid: float | None
    ask: float | None
    last: float | None
    mark: float | None
    implied_volatility: float | None
    delta: float | None
    gamma: float | None
    theta: float | None
    vega: float | None
    open_interest: int | None
    volume: int | None
    multiplier: int = 100
    ib_contract_id: int | None = None


@dataclass(slots=True)
class OptionChainData:
    provider: str
    symbol: str
    name: str | None
    exchange: str | None
    currency: str
    as_of: datetime
    quotes: list[OptionQuoteData]
    underlying_price: float | None = None
    warnings: list[str] | None = None


@dataclass(slots=True)
class OptionContractReference:
    symbol: str
    expiration_date: date
    right: str
    strike: float
    multiplier: int
    ib_contract_id: int | None
    exchange: str = "SMART"
    currency: str = "USD"


@dataclass(slots=True)
class HistoricalBarData:
    bar_date: date
    open: float
    high: float
    low: float
    close: float
    volume: int | None


@dataclass(slots=True)
class OptionHistoryData:
    provider: str
    bars: list[HistoricalBarData]


class MarketDataBroker(ABC):
    @abstractmethod
    def get_connection_status(self) -> BrokerStatus:
        raise NotImplementedError

    @abstractmethod
    def fetch_option_chain(
        self,
        symbol: str,
        strike: float | None = None,
        expiration_count: int | None = None,
    ) -> OptionChainData:
        raise NotImplementedError

    @abstractmethod
    def fetch_option_history(self, contract: OptionContractReference, duration_months: int) -> OptionHistoryData:
        raise NotImplementedError


class MarketDataBrokerError(RuntimeError):
    pass


class MarketDataConfigurationError(MarketDataBrokerError):
    pass


class MarketDataUnavailableError(MarketDataBrokerError):
    pass
