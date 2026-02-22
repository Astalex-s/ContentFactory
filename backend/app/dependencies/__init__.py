"""FastAPI dependencies."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.database import DatabaseRepository
from app.repositories.generated_content import GeneratedContentRepository
from app.repositories.product import ProductRepository
from app.services.content_service import ContentService
from app.services.health import HealthService
from app.services.image.image_generation_service import ImageGenerationService
from app.services.marketplace_import import MarketplaceImportService
from app.services.media import MediaStorageService
from app.services.product import ProductService
from app.services.text_generation_service import TextGenerationService
from app.services.video.video_generation_service import VideoGenerationService


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


def get_content_service(
    db: AsyncSession = Depends(get_db),
) -> ContentService:
    """Dependency: ContentService instance."""
    return ContentService(GeneratedContentRepository(db))


def get_marketplace_import_service(
    db: AsyncSession = Depends(get_db),
) -> MarketplaceImportService:
    """Dependency: MarketplaceImportService instance."""
    return MarketplaceImportService(ProductRepository(db))


def get_media_storage() -> MediaStorageService:
    """Dependency: MediaStorageService instance."""
    return MediaStorageService()


def get_image_generation_service(
    db: AsyncSession = Depends(get_db),
    media: MediaStorageService = Depends(get_media_storage),
) -> ImageGenerationService:
    """Dependency: ImageGenerationService instance."""
    return ImageGenerationService(
        ProductRepository(db),
        GeneratedContentRepository(db),
        media,
    )


def get_video_generation_service(
    db: AsyncSession = Depends(get_db),
    media: MediaStorageService = Depends(get_media_storage),
) -> VideoGenerationService:
    """Dependency: VideoGenerationService instance."""
    return VideoGenerationService(
        ProductRepository(db),
        GeneratedContentRepository(db),
        media,
    )


__all__ = [
    "get_content_service",
    "get_db",
    "get_health_service",
    "get_image_generation_service",
    "get_marketplace_import_service",
    "get_media_storage",
    "get_product_service",
    "get_text_generation_service",
    "get_video_generation_service",
]
