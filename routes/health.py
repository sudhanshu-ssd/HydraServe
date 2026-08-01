from fastapi import APIRouter
from sqlalchemy import text
from datetime import datetime, UTC
import time

from dependencies import database
import redis_config
from app_state import APP_START_TIME
from schema import HealthResponse

router = APIRouter(
    prefix="/health",
    tags=["health"]
)


@router.get("", response_model=HealthResponse)
async def health_check(
    db: database,
):
    postgres = "healthy"
    redis = "healthy"

    # PostgreSQL
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        postgres = "unhealthy"

    # Redis
    try:
        await redis_config.redis_client.ping()
    except Exception:
        redis = "unhealthy"

    overall = (
        "healthy"
        if postgres == "healthy" and redis == "healthy"
        else "degraded"
    )

    return HealthResponse(
        status=overall,
        version="1.0.0",
        uptime_seconds=int(time.time() - APP_START_TIME),
        timestamp=datetime.now(UTC),
        services={
            "postgres": postgres,
            "redis": redis,
        },
    )