"""FastAPI dependencies."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.database import DatabaseRepository
from app.repositories.generated_content import GeneratedContentRepository
from app.repositories.product import ProductRepository
from app.services.health import HealthService
from app.services.product import ProductService
from app.services.text_generation_service import TextGenerationService


def get_product_service(db: AsyncSession = Depends(get_db)) -> ProductService:
    """Dependency: ProductService instance."""
    return ProductService(ProductRepository(db))


def get_health_service(db: AsyncSession = Depends(get_db)) -> HealthService:
    """Dependency: HealthService instance."""
    return HealthService(DatabaseRepository(db))


def get_text_generation_service(
    db: AsyncSession = Depends(get_db),
) -> TextGenerationService:
    """Dependency: TextGenerationService instance."""
    return TextGenerationService(
        ProductRepository(db),
        GeneratedContentRepository(db),
    )


__all__ = [
    "get_db",
    "get_health_service",
    "get_product_service",
    "get_text_generation_service",
]
