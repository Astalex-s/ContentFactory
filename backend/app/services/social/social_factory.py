"""Factory for social platform providers."""

from __future__ import annotations

from app.models.social_account import SocialPlatform
from app.services.social.base_provider import BaseSocialProvider
from app.services.social.rutube_provider import RutubeProvider
from app.services.social.vk_provider import VKProvider
from app.services.social.youtube_provider import YouTubeProvider


def get_provider(platform: SocialPlatform) -> BaseSocialProvider:
    """Return provider instance for platform."""
    if platform == SocialPlatform.YOUTUBE:
        return YouTubeProvider()
    if platform == SocialPlatform.VK:
        return VKProvider()
    if platform == SocialPlatform.RUTUBE:
        return RutubeProvider()
    raise ValueError(f"Unsupported platform: {platform}")
