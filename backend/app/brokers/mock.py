from datetime import date, datetime, timezone

from app.brokers.base import BrokerStatus, MarketDataBroker, OptionChainData, OptionQuoteData


class MockMarketDataBroker(MarketDataBroker):
    def get_connection_status(self) -> BrokerStatus:
        return BrokerStatus(
            provider="mock",
            configured=True,
            connected=True,
            message="Mock market data provider ready for local development.",
            supports_live_data=False,
            supports_option_chain_fetch=True,
        )

    def fetch_option_chain(self, symbol: str) -> OptionChainData:
        normalized_symbol = symbol.upper()
        as_of = datetime.now(timezone.utc).replace(microsecond=0)

        chain_templates = {
            "AAPL": self._build_aapl_chain(),
            "SPY": self._build_spy_chain(),
        }
        quotes = chain_templates.get(normalized_symbol, self._build_generic_chain(normalized_symbol))

        return OptionChainData(
            provider="mock",
            symbol=normalized_symbol,
            name=f"{normalized_symbol} Holdings",
            exchange="SMART",
            currency="USD",
            as_of=as_of,
            quotes=quotes,
        )

    def _build_aapl_chain(self) -> list[OptionQuoteData]:
        return [
            self._quote(date(2026, 8, 21), "C", 215, 4.75, 5.05, 4.92, 4.90, 0.27, 0.44, 0.03, -0.07, 0.11, 1240, 580),
            self._quote(date(2026, 8, 21), "P", 205, 3.95, 4.20, 4.10, 4.08, 0.29, -0.39, 0.02, -0.06, 0.10, 980, 420),
            self._quote(date(2026, 9, 18), "C", 220, 5.85, 6.20, 6.00, 6.03, 0.26, 0.42, 0.02, -0.06, 0.13, 860, 310),
            self._quote(date(2026, 9, 18), "P", 200, 4.60, 4.95, 4.80, 4.77, 0.30, -0.36, 0.02, -0.05, 0.12, 730, 275),
        ]

    def _build_spy_chain(self) -> list[OptionQuoteData]:
        return [
            self._quote(date(2026, 8, 21), "C", 655, 8.10, 8.45, 8.25, 8.28, 0.18, 0.47, 0.01, -0.11, 0.18, 5000, 2400),
            self._quote(date(2026, 8, 21), "P", 620, 6.40, 6.75, 6.58, 6.57, 0.20, -0.31, 0.01, -0.08, 0.16, 4200, 2100),
            self._quote(date(2026, 9, 18), "C", 660, 10.50, 10.95, 10.70, 10.73, 0.19, 0.45, 0.01, -0.10, 0.21, 3600, 1900),
            self._quote(date(2026, 9, 18), "P", 615, 8.75, 9.10, 8.95, 8.93, 0.21, -0.29, 0.01, -0.07, 0.19, 3550, 1600),
        ]

    def _build_generic_chain(self, symbol: str) -> list[OptionQuoteData]:
        return [
            self._quote(date(2026, 8, 21), "C", 100, 2.10, 2.35, 2.20, 2.22, 0.24, 0.41, 0.02, -0.05, 0.07, 200, 75),
            self._quote(date(2026, 8, 21), "P", 95, 1.85, 2.05, 1.95, 1.95, 0.25, -0.34, 0.02, -0.04, 0.07, 180, 68),
        ]

    def _quote(
        self,
        expiration_date: date,
        right: str,
        strike: float,
        bid: float,
        ask: float,
        last: float,
        mark: float,
        implied_volatility: float,
        delta: float,
        gamma: float,
        theta: float,
        vega: float,
        open_interest: int,
        volume: int,
    ) -> OptionQuoteData:
        return OptionQuoteData(
            expiration_date=expiration_date,
            right=right,
            strike=strike,
            bid=bid,
            ask=ask,
            last=last,
            mark=mark,
            implied_volatility=implied_volatility,
            delta=delta,
            gamma=gamma,
            theta=theta,
            vega=vega,
            open_interest=open_interest,
            volume=volume,
        )
