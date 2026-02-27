"""Abstract base class for social platform providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class VideoUploadMetadata:
    """Metadata for video upload."""

    def __init__(
        self,
        title: str,
        description: str = "",
        tags: list[str] | None = None,
        privacy_status: str = "private",
        **kwargs: Any,
    ):
        self.title = title
        self.description = description or ""
        self.tags = tags or []
        self.privacy_status = privacy_status
        self.extra = kwargs


class VideoUploadResult:
    """Result of video upload."""

    def __init__(
        self,
        video_id: str,
        status: str,
        published_at: str | None = None,
        platform_url: str | None = None,
    ):
        self.video_id = video_id
        self.status = status
        self.published_at = published_at
        self.platform_url = platform_url


class BaseSocialProvider(ABC):
    """Abstract base for social platform providers. Provider does not know about HTTP.
    Service layer resolves account_id -> access_token and passes token to provider."""

    @abstractmethod
    async def upload_video(
        self,
        access_token: str,
        file_path: str,
        metadata: VideoUploadMetadata,
    ) -> VideoUploadResult:
        """Upload video to platform. access_token from OAuth. Raises on failure."""
        ...

    @abstractmethod
    async def check_video_status(
        self,
        access_token: str,
        video_id: str,
    ) -> str:
        """Check video publication status. Returns status string."""
        ...

    @abstractmethod
    async def fetch_video_stats(
        self,
        access_token: str,
        video_id: str,
    ) -> dict:
        """Fetch video statistics (views, clicks, etc.). Returns dict with metrics."""
        ...
