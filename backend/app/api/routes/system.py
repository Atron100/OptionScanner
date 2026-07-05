from pathlib import Path

from fastapi import APIRouter

from app.core.settings import get_settings

router = APIRouter()


@router.get("/system/info")
def system_info() -> dict[str, str]:
    settings = get_settings()
    database_path = settings.database_url.replace("sqlite:///", "", 1)
    return {
        "app_name": settings.app_name,
        "environment": settings.environment,
        "database_url": settings.database_url,
        "database_exists": str(Path(database_path).exists()).lower(),
    }

