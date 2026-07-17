from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models import (
    OptionChainSnapshot,
    OptionContract,
    OptionExpiration,
    OptionHistoricalBar,
    OptionQuoteSnapshot,
    Underlying,
)


class MarketDataRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_or_create_underlying(
        self,
        symbol: str,
        name: str | None,
        exchange: str | None,
        currency: str,
    ) -> Underlying:
        statement = select(Underlying).where(Underlying.symbol == symbol)
        underlying = self.db.execute(statement).scalar_one_or_none()
        if underlying is None:
            underlying = Underlying(symbol=symbol, name=name, exchange=exchange, currency=currency)
            self.db.add(underlying)
            self.db.flush()
            return underlying

        underlying.name = name
        underlying.exchange = exchange
        underlying.currency = currency
        self.db.flush()
        return underlying

    def get_or_create_expiration(self, underlying_id: int, expiration_date: date) -> OptionExpiration:
        statement = select(OptionExpiration).where(
            OptionExpiration.underlying_id == underlying_id,
            OptionExpiration.expiration_date == expiration_date,
        )
        expiration = self.db.execute(statement).scalar_one_or_none()
        if expiration is None:
            expiration = OptionExpiration(underlying_id=underlying_id, expiration_date=expiration_date)
            self.db.add(expiration)
            self.db.flush()
        return expiration

    def get_or_create_contract(
        self,
        underlying_id: int,
        expiration_id: int,
        right: str,
        strike: float,
        multiplier: int,
        ib_contract_id: int | None,
    ) -> OptionContract:
        statement = select(OptionContract).where(
            OptionContract.underlying_id == underlying_id,
            OptionContract.expiration_id == expiration_id,
            OptionContract.right == right,
            OptionContract.strike == strike,
        )
        contract = self.db.execute(statement).scalar_one_or_none()
        if contract is None:
            contract = OptionContract(
                underlying_id=underlying_id,
                expiration_id=expiration_id,
                right=right,
                strike=strike,
                multiplier=multiplier,
                ib_contract_id=ib_contract_id,
            )
            self.db.add(contract)
            self.db.flush()
            return contract

        contract.multiplier = multiplier
        if ib_contract_id is not None:
            contract.ib_contract_id = ib_contract_id
        self.db.flush()
        return contract

    def create_snapshot(
        self,
        underlying_id: int,
        provider: str,
        requested_symbol: str,
        as_of,
        underlying_price: float | None,
    ) -> OptionChainSnapshot:
        snapshot = OptionChainSnapshot(
            underlying_id=underlying_id,
            provider=provider,
            requested_symbol=requested_symbol,
            as_of=as_of,
            underlying_price=underlying_price,
        )
        self.db.add(snapshot)
        self.db.flush()
        return snapshot

    def add_quote_snapshot(
        self,
        snapshot_id: int,
        contract_id: int,
        bid: float | None,
        ask: float | None,
        last: float | None,
        mark: float | None,
        implied_volatility: float | None,
        delta: float | None,
        gamma: float | None,
        theta: float | None,
        vega: float | None,
        open_interest: int | None,
        volume: int | None,
    ) -> OptionQuoteSnapshot:
        quote_snapshot = OptionQuoteSnapshot(
            chain_snapshot_id=snapshot_id,
            contract_id=contract_id,
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
        self.db.add(quote_snapshot)
        self.db.flush()
        return quote_snapshot

    def get_latest_chain(self, symbol: str) -> OptionChainSnapshot | None:
        statement = (
            select(OptionChainSnapshot)
            .join(Underlying)
            .where(Underlying.symbol == symbol.upper())
            .options(
                selectinload(OptionChainSnapshot.underlying),
                selectinload(OptionChainSnapshot.quote_snapshots)
                .selectinload(OptionQuoteSnapshot.contract)
                .selectinload(OptionContract.expiration),
            )
            .order_by(OptionChainSnapshot.as_of.desc(), OptionChainSnapshot.id.desc())
        )
        return self.db.execute(statement).scalars().first()

    def get_latest_chains(self) -> list[OptionChainSnapshot]:
        statement = (
            select(OptionChainSnapshot)
            .options(
                selectinload(OptionChainSnapshot.underlying),
                selectinload(OptionChainSnapshot.quote_snapshots),
            )
            .order_by(OptionChainSnapshot.as_of.desc(), OptionChainSnapshot.id.desc())
        )
        latest_by_underlying: dict[int, OptionChainSnapshot] = {}
        for snapshot in self.db.execute(statement).scalars():
            latest_by_underlying.setdefault(snapshot.underlying_id, snapshot)
        return sorted(latest_by_underlying.values(), key=lambda snapshot: snapshot.underlying.symbol)

    def get_contract(self, symbol: str, expiration_date: date, right: str, strike: float) -> OptionContract | None:
        statement = (
            select(OptionContract)
            .join(OptionContract.underlying)
            .join(OptionContract.expiration)
            .where(
                Underlying.symbol == symbol.upper(),
                OptionExpiration.expiration_date == expiration_date,
                OptionContract.right == right.upper(),
                OptionContract.strike == strike,
            )
            .options(selectinload(OptionContract.underlying), selectinload(OptionContract.expiration))
        )
        return self.db.execute(statement).unique().scalar_one_or_none()

    def upsert_historical_bar(self, contract_id: int, provider: str, bar) -> OptionHistoricalBar:
        statement = select(OptionHistoricalBar).where(
            OptionHistoricalBar.contract_id == contract_id,
            OptionHistoricalBar.provider == provider,
            OptionHistoricalBar.bar_date == bar.bar_date,
        )
        historical_bar = self.db.execute(statement).scalar_one_or_none()
        if historical_bar is None:
            historical_bar = OptionHistoricalBar(contract_id=contract_id, provider=provider, bar_date=bar.bar_date)
            self.db.add(historical_bar)

        historical_bar.open = bar.open
        historical_bar.high = bar.high
        historical_bar.low = bar.low
        historical_bar.close = bar.close
        historical_bar.volume = bar.volume
        self.db.flush()
        return historical_bar

    def get_historical_bars(self, contract_id: int) -> list[OptionHistoricalBar]:
        statement = (
            select(OptionHistoricalBar)
            .where(OptionHistoricalBar.contract_id == contract_id)
            .order_by(OptionHistoricalBar.bar_date)
        )
        return list(self.db.execute(statement).scalars())
