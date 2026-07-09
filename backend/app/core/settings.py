from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="OPTIONSCANNER_",
        env_file=".env",
        extra="ignore",
    )

    app_name: str = "OptionScanner API"
    app_version: str = "0.1.0"
    environment: str = "development"
    api_prefix: str = "/api/v1"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_cors_origins: str = Field(default="http://localhost:5173")
    database_url: str = "sqlite:///./data/optionscanner.db"
    log_level: str = "INFO"
    market_data_provider: str = "mock"
    ibkr_host: str = "127.0.0.1"
    ibkr_port: int = 7497
    ibkr_client_id: int = 1
    ibkr_read_only: bool = True

    @property
    def api_cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.api_cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
