"""Health check endpoints."""

from fastapi import APIRouter, Depends

from app.dependencies import get_health_service
from app.services.health import HealthService

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health() -> dict:
    """Basic liveness/readiness check."""
    return {"status": "ok"}


@router.get("/db")
async def health_db(service: HealthService = Depends(get_health_service)) -> dict:
    """Check database connectivity."""
    connected = await service.check_database()
    return {"status": "ok", "database": "connected" if connected else "disconnected"}
