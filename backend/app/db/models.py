from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AppState(Base):
    __tablename__ = "app_state"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str] = mapped_column(String(500), nullable=False)


class Underlying(Base):
    __tablename__ = "underlyings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    exchange: Mapped[str | None] = mapped_column(String(64), nullable=True)
    currency: Mapped[str] = mapped_column(String(8), default="USD")

    expirations: Mapped[list["OptionExpiration"]] = relationship(back_populates="underlying")
    contracts: Mapped[list["OptionContract"]] = relationship(back_populates="underlying")
    snapshots: Mapped[list["OptionChainSnapshot"]] = relationship(back_populates="underlying")


class OptionExpiration(Base):
    __tablename__ = "option_expirations"
    __table_args__ = (UniqueConstraint("underlying_id", "expiration_date", name="uq_underlying_expiration"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    underlying_id: Mapped[int] = mapped_column(ForeignKey("underlyings.id"), index=True)
    expiration_date: Mapped[date] = mapped_column(Date, index=True)

    underlying: Mapped[Underlying] = relationship(back_populates="expirations")
    contracts: Mapped[list["OptionContract"]] = relationship(back_populates="expiration")


class OptionContract(Base):
    __tablename__ = "option_contracts"
    __table_args__ = (
        UniqueConstraint(
            "underlying_id",
            "expiration_id",
            "right",
            "strike",
            name="uq_contract_definition",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    underlying_id: Mapped[int] = mapped_column(ForeignKey("underlyings.id"), index=True)
    expiration_id: Mapped[int] = mapped_column(ForeignKey("option_expirations.id"), index=True)
    right: Mapped[str] = mapped_column(String(4), index=True)
    strike: Mapped[float] = mapped_column(Float, index=True)
    multiplier: Mapped[int] = mapped_column(Integer, default=100)
    ib_contract_id: Mapped[int | None] = mapped_column(Integer, nullable=True, unique=True)

    underlying: Mapped[Underlying] = relationship(back_populates="contracts")
    expiration: Mapped[OptionExpiration] = relationship(back_populates="contracts")
    quote_snapshots: Mapped[list["OptionQuoteSnapshot"]] = relationship(back_populates="contract")


class OptionChainSnapshot(Base):
    __tablename__ = "option_chain_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    underlying_id: Mapped[int] = mapped_column(ForeignKey("underlyings.id"), index=True)
    provider: Mapped[str] = mapped_column(String(32))
    requested_symbol: Mapped[str] = mapped_column(String(32), index=True)
    as_of: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)

    underlying: Mapped[Underlying] = relationship(back_populates="snapshots")
    quote_snapshots: Mapped[list["OptionQuoteSnapshot"]] = relationship(back_populates="chain_snapshot")


class OptionQuoteSnapshot(Base):
    __tablename__ = "option_quote_snapshots"
    __table_args__ = (UniqueConstraint("chain_snapshot_id", "contract_id", name="uq_snapshot_contract"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chain_snapshot_id: Mapped[int] = mapped_column(ForeignKey("option_chain_snapshots.id"), index=True)
    contract_id: Mapped[int] = mapped_column(ForeignKey("option_contracts.id"), index=True)
    bid: Mapped[float | None] = mapped_column(Float, nullable=True)
    ask: Mapped[float | None] = mapped_column(Float, nullable=True)
    last: Mapped[float | None] = mapped_column(Float, nullable=True)
    mark: Mapped[float | None] = mapped_column(Float, nullable=True)
    implied_volatility: Mapped[float | None] = mapped_column(Float, nullable=True)
    delta: Mapped[float | None] = mapped_column(Float, nullable=True)
    gamma: Mapped[float | None] = mapped_column(Float, nullable=True)
    theta: Mapped[float | None] = mapped_column(Float, nullable=True)
    vega: Mapped[float | None] = mapped_column(Float, nullable=True)
    open_interest: Mapped[int | None] = mapped_column(Integer, nullable=True)
    volume: Mapped[int | None] = mapped_column(Integer, nullable=True)

    contract: Mapped[OptionContract] = relationship(back_populates="quote_snapshots")
    chain_snapshot: Mapped[OptionChainSnapshot] = relationship(back_populates="quote_snapshots")
