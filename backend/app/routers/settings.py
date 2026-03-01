"""Settings router."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.publish_rate_limit import set_publish_rate_limit_enabled
from app.repositories.app_settings import AppSettingsRepository

router = APIRouter(prefix="/settings", tags=["settings"])


class SettingsRead(BaseModel):
    """Settings response."""

    auto_publish: bool = False
    publish_rate_limit_enabled: bool = True


class SettingsUpdate(BaseModel):
    """Settings update request."""

    auto_publish: bool | None = None
    publish_rate_limit_enabled: bool | None = None


@router.get("", response_model=SettingsRead)
async def get_settings(
    db: AsyncSession = Depends(get_db),
) -> SettingsRead:
    """Get app settings."""
    repo = AppSettingsRepository(db)
    auto_val = await repo.get("auto_publish")
    rate_val = await repo.get("publish_rate_limit_enabled")
    return SettingsRead(
        auto_publish=auto_val == "true",
        publish_rate_limit_enabled=rate_val != "false",
    )


@router.patch("", response_model=SettingsRead)
async def update_settings(
    body: SettingsUpdate,
    db: AsyncSession = Depends(get_db),
) -> SettingsRead:
    """Update app settings."""
    repo = AppSettingsRepository(db)
    if body.auto_publish is not None:
        await repo.set("auto_publish", "true" if body.auto_publish else "false")
    if body.publish_rate_limit_enabled is not None:
        val = "true" if body.publish_rate_limit_enabled else "false"
        await repo.set("publish_rate_limit_enabled", val)
        set_publish_rate_limit_enabled(body.publish_rate_limit_enabled)
    await db.commit()
    auto_val = await repo.get("auto_publish")
    rate_val = await repo.get("publish_rate_limit_enabled")
    return SettingsRead(
        auto_publish=auto_val == "true",
        publish_rate_limit_enabled=rate_val != "false",
    )
