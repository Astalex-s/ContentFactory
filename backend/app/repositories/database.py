"""Database repository for low-level DB operations."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class DatabaseRepository:
    """Repository for database-level operations (e.g. health check)."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def ping(self) -> bool:
        """Check database connectivity."""
        result = await self.session.execute(text("SELECT 1"))
        return result.scalar() is not None
