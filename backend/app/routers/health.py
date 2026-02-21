"""Health check endpoints."""

from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health() -> dict:
    """Basic liveness/readiness check."""
    return {"status": "ok"}
