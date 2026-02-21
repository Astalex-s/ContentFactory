"""Repository layer — DB operations only."""

from app.repositories.generated_content import GeneratedContentRepository
from app.repositories.product import ProductRepository

__all__ = ["GeneratedContentRepository", "ProductRepository"]
