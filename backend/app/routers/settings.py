"""Settings router."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.app_settings import AppSettingsRepository

router = APIRouter(prefix="/settings", tags=["settings"])


class SettingsRead(BaseModel):
    """Settings response."""

    auto_publish: bool = False


class SettingsUpdate(BaseModel):
    """Settings update request."""

    auto_publish: bool | None = None


@router.get("", response_model=SettingsRead)
async def get_settings(
    db: AsyncSession = Depends(get_db),
) -> SettingsRead:
    """Get app settings."""
    repo = AppSettingsRepository(db)
    val = await repo.get("auto_publish")
    return SettingsRead(auto_publish=val == "true")


@router.patch("", response_model=SettingsRead)
async def update_settings(
    body: SettingsUpdate,
    db: AsyncSession = Depends(get_db),
) -> SettingsRead:
    """Update app settings."""
    repo = AppSettingsRepository(db)
    if body.auto_publish is not None:
        await repo.set("auto_publish", "true" if body.auto_publish else "false")
    await db.commit()
    val = await repo.get("auto_publish")
    return SettingsRead(auto_publish=val == "true")
