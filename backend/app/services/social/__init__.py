"""Social platform services: OAuth, providers, factory."""

from app.services.social.base_provider import (
    BaseSocialProvider,
    VideoUploadMetadata,
    VideoUploadResult,
)
from app.services.social.oauth_service import OAuthService
from app.services.social.social_factory import get_provider

__all__ = [
    "BaseSocialProvider",
    "OAuthService",
    "VideoUploadMetadata",
    "VideoUploadResult",
    "get_provider",
]
