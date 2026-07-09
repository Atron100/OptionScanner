from pydantic import BaseModel


class BrokerStatusResponse(BaseModel):
    provider: str
    configured: bool
    connected: bool
    message: str
    host: str | None = None
    port: int | None = None
    read_only: bool | None = None
    supports_live_data: bool = False
    supports_option_chain_fetch: bool = False
