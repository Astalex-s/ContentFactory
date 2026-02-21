"""FastAPI dependencies."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.database import DatabaseRepository
from app.repositories.product import ProductRepository
from app.services.health import HealthService
from app.services.product import ProductService


def get_product_service(db: AsyncSession = Depends(get_db)) -> ProductService:
    """Dependency: ProductService instance."""
    return ProductService(ProductRepository(db))


def get_health_service(db: AsyncSession = Depends(get_db)) -> HealthService:
    """Dependency: HealthService instance."""
    return HealthService(DatabaseRepository(db))


__all__ = ["get_db", "get_health_service", "get_product_service"]
