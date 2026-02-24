"""VK provider: video.save -> upload_url -> upload file -> confirm."""

from __future__ import annotations

import logging
from pathlib import Path

import httpx

from app.core.config import get_settings
from app.services.social.base_provider import (
    BaseSocialProvider,
    VideoUploadMetadata,
    VideoUploadResult,
)

log = logging.getLogger(__name__)

VK_API_BASE = "https://api.vk.ru/method"
VK_API_VERSION = "5.131"


class VKProvider(BaseSocialProvider):
    """VK video upload: video.save -> upload_url -> POST file."""

    def __init__(self):
        self.settings = get_settings()
        self._timeout = self.settings.SOCIAL_TIMEOUT

    async def upload_video(
        self,
        access_token: str,
        file_path: str,
        metadata: VideoUploadMetadata,
    ) -> VideoUploadResult:
        """1) video.save -> upload_url 2) POST file 3) response has video_id."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Video file not found: {file_path}")

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(
                f"{VK_API_BASE}/video.save",
                params={
                    "access_token": access_token,
                    "v": VK_API_VERSION,
                    "name": metadata.title[:128],
                    "description": (metadata.description or "")[:5000],
                },
            )
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            err = data["error"]
            log.warning("VK video.save error: %s", err)
            raise ValueError(err.get("error_msg", "VK video.save failed"))

        upload_url = data.get("response", {}).get("upload_url")
        if not upload_url:
            raise ValueError("VK did not return upload_url")

        with open(path, "rb") as f:
            files = {"video_file": (path.name, f, "video/mp4")}
            async with httpx.AsyncClient(timeout=httpx.Timeout(300.0)) as client:
                upload_resp = await client.post(upload_url, files=files)

        upload_resp.raise_for_status()
        upload_data = upload_resp.json()

        video_id = str(upload_data.get("video_id", ""))
        owner_id = upload_data.get("owner_id", "")
        if owner_id and video_id:
            full_id = f"{owner_id}_{video_id}"
        else:
            full_id = video_id or "unknown"

        return VideoUploadResult(
            video_id=full_id,
            status="uploaded",
            published_at=None,
            platform_url=f"https://vk.com/video{full_id}" if full_id != "unknown" else None,
        )

    async def check_video_status(
        self,
        access_token: str,
        video_id: str,
    ) -> str:
        """Check video status via video.get."""
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(
                f"{VK_API_BASE}/video.get",
                params={
                    "access_token": access_token,
                    "v": VK_API_VERSION,
                    "videos": video_id,
                },
            )
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            return "unknown"
        items = data.get("response", {}).get("items", [])
        if not items:
            return "unknown"
        item = items[0]
        processing = item.get("processing", 0)
        if processing == 1:
            return "processing"
        return "available"
