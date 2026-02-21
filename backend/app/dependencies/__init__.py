"""FastAPI dependencies."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.product import ProductRepository
from app.services.product import ProductService


def get_product_service(db: AsyncSession = Depends(get_db)) -> ProductService:
    """Dependency: ProductService instance."""
    return ProductService(ProductRepository(db))


__all__ = ["get_db", "get_product_service"]
