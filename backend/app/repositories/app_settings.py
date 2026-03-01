"""App settings repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.app_settings import AppSettings


class AppSettingsRepository:
    """Repository for app settings key-value store."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, key: str) -> str | None:
        """Get value by key."""
        result = await self.session.execute(select(AppSettings).where(AppSettings.key == key))
        row = result.scalar_one_or_none()
        return row.value if row else None

    async def set(self, key: str, value: str) -> None:
        """Set value for key (upsert)."""
        result = await self.session.execute(select(AppSettings).where(AppSettings.key == key))
        row = result.scalar_one_or_none()
        if row:
            row.value = value
        else:
            self.session.add(AppSettings(key=key, value=value))
        await self.session.flush()
