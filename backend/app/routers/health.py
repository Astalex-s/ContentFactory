"""Health check endpoints."""

from sqlalchemy import text

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health() -> dict:
    """Basic liveness/readiness check."""
    return {"status": "ok"}


@router.get("/db")
async def health_db(db: AsyncSession = Depends(get_db)) -> dict:
    """Check database connectivity."""
    await db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}
