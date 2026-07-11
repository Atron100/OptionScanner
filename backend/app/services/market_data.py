from app.brokers.base import MarketDataBroker, OptionContractReference
from app.brokers.base import MarketDataUnavailableError
from app.repositories.market_data import MarketDataRepository
from app.schemas.market_data import (
    ChainSnapshotResponse,
    ContractQuoteResponse,
    HistoricalBarResponse,
    HistoricalBarsResponse,
    IngestChainResponse,
)


class MarketDataIngestionService:
    def __init__(self, db, broker: MarketDataBroker) -> None:
        self.db = db
        self.broker = broker
        self.repository = MarketDataRepository(db)

    def ingest_symbol(
        self,
        symbol: str,
        strike: float | None = None,
        expiration_count: int | None = None,
    ) -> IngestChainResponse:
        chain = self.broker.fetch_option_chain(symbol, strike, expiration_count)
        underlying = self.repository.get_or_create_underlying(
            symbol=chain.symbol,
            name=chain.name,
            exchange=chain.exchange,
            currency=chain.currency,
        )
        snapshot = self.repository.create_snapshot(
            underlying_id=underlying.id,
            provider=chain.provider,
            requested_symbol=symbol.upper(),
            as_of=chain.as_of,
        )

        expiration_dates: set = set()
        contract_ids: set[int] = set()
        for quote in chain.quotes:
            expiration = self.repository.get_or_create_expiration(underlying.id, quote.expiration_date)
            expiration_dates.add(expiration.expiration_date)
            contract = self.repository.get_or_create_contract(
                underlying_id=underlying.id,
                expiration_id=expiration.id,
                right=quote.right,
                strike=quote.strike,
                multiplier=quote.multiplier,
                ib_contract_id=quote.ib_contract_id,
            )
            contract_ids.add(contract.id)
            self.repository.add_quote_snapshot(
                snapshot_id=snapshot.id,
                contract_id=contract.id,
                bid=quote.bid,
                ask=quote.ask,
                last=quote.last,
                mark=quote.mark,
                implied_volatility=quote.implied_volatility,
                delta=quote.delta,
                gamma=quote.gamma,
                theta=quote.theta,
                vega=quote.vega,
                open_interest=quote.open_interest,
                volume=quote.volume,
            )

        self.db.commit()

        return IngestChainResponse(
            symbol=chain.symbol,
            provider=chain.provider,
            snapshot_id=snapshot.id,
            contract_count=len(contract_ids),
            quote_count=len(chain.quotes),
            expirations=sorted(expiration_dates),
            as_of=chain.as_of,
            warnings=chain.warnings or [],
        )


class MarketDataQueryService:
    def __init__(self, db) -> None:
        self.repository = MarketDataRepository(db)

    def get_latest_chain(self, symbol: str) -> ChainSnapshotResponse | None:
        snapshot = self.repository.get_latest_chain(symbol)
        if snapshot is None:
            return None

        contracts = [
            ContractQuoteResponse(
                expiration_date=quote.contract.expiration.expiration_date,
                right=quote.contract.right,
                strike=quote.contract.strike,
                bid=quote.bid,
                ask=quote.ask,
                last=quote.last,
                mark=quote.mark,
                implied_volatility=quote.implied_volatility,
                delta=quote.delta,
                gamma=quote.gamma,
                theta=quote.theta,
                vega=quote.vega,
                open_interest=quote.open_interest,
                volume=quote.volume,
            )
            for quote in sorted(
                snapshot.quote_snapshots,
                key=lambda item: (
                    item.contract.expiration.expiration_date,
                    item.contract.right,
                    item.contract.strike,
                ),
            )
        ]

        return ChainSnapshotResponse(
            symbol=snapshot.underlying.symbol,
            provider=snapshot.provider,
            as_of=snapshot.as_of,
            quote_count=len(contracts),
            contracts=contracts,
        )


class HistoricalOptionDataService:
    def __init__(self, db, broker: MarketDataBroker) -> None:
        self.db = db
        self.broker = broker
        self.repository = MarketDataRepository(db)

    def ingest_history(
        self,
        symbol: str,
        expiration_date,
        right: str,
        strike: float,
        duration_months: int,
    ) -> HistoricalBarsResponse:
        contract = self.repository.get_contract(symbol, expiration_date, right, strike)
        if contract is None:
            raise MarketDataUnavailableError(
                "Option contract was not found locally. Ingest its live chain before requesting historical bars."
            )

        history = self.broker.fetch_option_history(
            OptionContractReference(
                symbol=contract.underlying.symbol,
                expiration_date=contract.expiration.expiration_date,
                right=contract.right,
                strike=contract.strike,
                multiplier=contract.multiplier,
                ib_contract_id=contract.ib_contract_id,
                exchange=contract.underlying.exchange or "SMART",
                currency=contract.underlying.currency,
            ),
            duration_months,
        )
        for bar in history.bars:
            self.repository.upsert_historical_bar(contract.id, history.provider, bar)
        self.db.commit()

        bars = self.repository.get_historical_bars(contract.id)
        return HistoricalBarsResponse(
            symbol=contract.underlying.symbol,
            expiration_date=contract.expiration.expiration_date,
            right=contract.right,
            strike=contract.strike,
            provider=history.provider,
            bar_count=len(bars),
            bars=[
                HistoricalBarResponse(
                    bar_date=bar.bar_date,
                    open=bar.open,
                    high=bar.high,
                    low=bar.low,
                    close=bar.close,
                    volume=bar.volume,
                )
                for bar in bars
            ],
        )
