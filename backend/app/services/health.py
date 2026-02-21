"""Health check service."""

from app.repositories.database import DatabaseRepository


class HealthService:
    """Service for health checks."""

    def __init__(self, repository: DatabaseRepository):
        self.repository = repository

    async def check_database(self) -> bool:
        """Check database connectivity."""
        return await self.repository.ping()
