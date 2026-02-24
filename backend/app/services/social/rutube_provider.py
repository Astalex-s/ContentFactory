"""Rutube provider. No official upload API — read-only + NotImplementedError for upload."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.core.config import get_settings
from app.services.social.base_provider import (
    BaseSocialProvider,
    VideoUploadMetadata,
    VideoUploadResult,
)

log = logging.getLogger(__name__)

# Rutube has no official documented upload API. Read-only endpoints exist:
# https://rutube.ru/api/video/{id} - video info
# Upload: NotImplementedError with comment


class RutubeProvider(BaseSocialProvider):
    """Rutube: get_channel_videos, check_video_status. upload_video -> NotImplementedError."""

    def __init__(self):
        self.settings = get_settings()
        self._timeout = self.settings.SOCIAL_TIMEOUT

    async def upload_video(
        self,
        access_token: str,
        file_path: str,
        metadata: VideoUploadMetadata,
    ) -> VideoUploadResult:
        """Rutube has no official upload API. Raise NotImplementedError.
        See: no public upload documentation at rutube.ru. Community wrappers exist
        but are undocumented. When official API is available, implement here."""
        raise NotImplementedError(
            "Rutube upload API is not officially documented. "
            "Implement when Rutube provides upload API."
        )

    async def get_channel_videos(self, access_token: str, limit: int = 20) -> list[dict[str, Any]]:
        """Get videos from channel (read-only). Uses public API if available."""
        # Rutube public API: https://rutube.ru/api/video/ - may require different auth
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(
                "https://rutube.ru/api/video/",
                params={"limit": limit},
            )
        if resp.status_code != 200:
            return []
        data = resp.json()
        return data.get("results", [])

    async def check_video_status(
        self,
        access_token: str,
        video_id: str,
    ) -> str:
        """Check video status via Rutube public API."""
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(f"https://rutube.ru/api/video/{video_id}/")
        if resp.status_code != 200:
            return "unknown"
        data = resp.json()
        return data.get("status", "unknown")
