from pathlib import Path

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session, sessionmaker

from app.core.settings import get_settings
from app.db.base import Base
from app.db import models  # noqa: F401

settings = get_settings()
engine = create_engine(settings.database_url, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def initialize_database() -> None:
    database_url = settings.database_url
    if database_url.startswith("sqlite:///"):
        database_path = Path(database_url.replace("sqlite:///", "", 1))
        database_path.parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    if database_url.startswith("sqlite:///"):
        columns = {column["name"] for column in inspect(engine).get_columns("option_chain_snapshots")}
        if "underlying_price" not in columns:
            with engine.begin() as connection:
                connection.exec_driver_sql("ALTER TABLE option_chain_snapshots ADD COLUMN underlying_price FLOAT")


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
