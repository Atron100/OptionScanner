from fastapi import APIRouter

from app.api.routes.brokers import router as broker_router
from app.api.routes.health import router as health_router
from app.api.routes.market_data import router as market_data_router
from app.api.routes.scanner import router as scanner_router
from app.api.routes.system import router as system_router
from app.api.routes.strategies import router as strategies_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(system_router, tags=["system"])
api_router.include_router(broker_router, tags=["brokers"])
api_router.include_router(market_data_router, tags=["market-data"])
api_router.include_router(strategies_router, tags=["strategies"])
api_router.include_router(scanner_router, tags=["scanner"])
