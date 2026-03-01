"""FastAPI dependencies."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.analytics import AnalyticsRepository
from app.repositories.database import DatabaseRepository
from app.repositories.generated_content import GeneratedContentRepository
from app.repositories.oauth_app_credentials import OAuthAppCredentialsRepository
from app.repositories.product import ProductRepository
from app.repositories.publication_queue import PublicationQueueRepository
from app.repositories.social_account import SocialAccountRepository
from app.services.analytics_service import AnalyticsService
from app.services.content_service import ContentService
from app.services.health import HealthService
from app.services.image.image_generation_service import ImageGenerationService
from app.services.marketplace_import import MarketplaceImportService
from app.services.media import get_storage
from app.services.product import ProductService
from app.services.publication_service import PublicationService
from app.services.recommendation_service import RecommendationService
from app.services.social.oauth_app_credentials_service import OAuthAppCredentialsService
from app.services.social.oauth_service import OAuthService
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


def get_media_storage():
    """Dependency: StorageInterface (LocalFileStorage or S3Storage)."""
    return get_storage()


def get_image_generation_service(
    db: AsyncSession = Depends(get_db),
    media=Depends(get_media_storage),
) -> ImageGenerationService:
    """Dependency: ImageGenerationService instance."""
    return ImageGenerationService(
        ProductRepository(db),
        GeneratedContentRepository(db),
        media,
    )


def get_video_generation_service(
    db: AsyncSession = Depends(get_db),
    media=Depends(get_media_storage),
) -> VideoGenerationService:
    """Dependency: VideoGenerationService instance."""
    return VideoGenerationService(
        ProductRepository(db),
        GeneratedContentRepository(db),
        media,
    )


def get_oauth_service(db: AsyncSession = Depends(get_db)) -> OAuthService:
    """Dependency: OAuthService instance."""
    return OAuthService(db)


def get_publication_service(
    db: AsyncSession = Depends(get_db),
    oauth: OAuthService = Depends(get_oauth_service),
    storage=Depends(get_media_storage),
) -> PublicationService:
    """Dependency: PublicationService instance."""
    return PublicationService(
        PublicationQueueRepository(db),
        GeneratedContentRepository(db),
        SocialAccountRepository(db),
        ProductRepository(db),
        oauth_service=oauth,
        storage=storage,
    )


def get_analytics_service(
    db: AsyncSession = Depends(get_db),
) -> AnalyticsService:
    """Dependency: AnalyticsService instance."""
    return AnalyticsService(AnalyticsRepository(db))


def get_social_account_repository(
    db: AsyncSession = Depends(get_db),
) -> SocialAccountRepository:
    """Dependency: SocialAccountRepository instance."""
    return SocialAccountRepository(db)


def get_publication_queue_repository(
    db: AsyncSession = Depends(get_db),
) -> PublicationQueueRepository:
    """Dependency: PublicationQueueRepository instance."""
    return PublicationQueueRepository(db)


def get_recommendation_service(
    db: AsyncSession = Depends(get_db),
) -> RecommendationService:
    """Dependency: RecommendationService instance."""
    return RecommendationService(
        AnalyticsRepository(db),
        GeneratedContentRepository(db),
        ProductRepository(db),
    )


def get_oauth_app_credentials_service(
    db: AsyncSession = Depends(get_db),
) -> OAuthAppCredentialsService:
    """Dependency: OAuthAppCredentialsService instance."""
    return OAuthAppCredentialsService(OAuthAppCredentialsRepository(db))


__all__ = [
    "get_analytics_service",
    "get_content_service",
    "get_db",
    "get_health_service",
    "get_publication_queue_repository",
    "get_image_generation_service",
    "get_marketplace_import_service",
    "get_media_storage",
    "get_oauth_app_credentials_service",
    "get_oauth_service",
    "get_product_service",
    "get_publication_service",
    "get_recommendation_service",
    "get_social_account_repository",
    "get_text_generation_service",
    "get_video_generation_service",
]
