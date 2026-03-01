"""VK provider: video.save -> upload_url -> upload file -> confirm.

VK ID приложения не имеют доступа к video.save для личных страниц.
Загрузка видео идёт через токен сообщества (VK_COMMUNITY_TOKEN) + group_id.
Токен сообщества получается вручную: Управление сообществом → Работа с API → Создать ключ.
"""

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

VK_API_BASE = "https://api.vk.com/method"
VK_API_VERSION = "5.199"


class VKProvider(BaseSocialProvider):
    """VK video upload via community token + group_id."""

    def __init__(self):
        self.settings = get_settings()
        self._timeout = self.settings.SOCIAL_TIMEOUT

    def _get_upload_token(self) -> str:
        """Возвращает токен для video.save: community > service_key > access_token."""
        if self.settings.VK_COMMUNITY_TOKEN:
            return self.settings.VK_COMMUNITY_TOKEN
        if self.settings.VK_SERVICE_KEY:
            return self.settings.VK_SERVICE_KEY
        raise ValueError(
            "VK_COMMUNITY_TOKEN не задан. Получите токен сообщества: "
            "Управление сообществом → Работа с API → Создать ключ (права: видео)."
        )

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

        upload_token = self._get_upload_token()
        group_id = self.settings.VK_GROUP_ID
        if not group_id:
            raise ValueError(
                "VK_GROUP_ID не задан. Укажите ID сообщества в .env для загрузки видео."
            )

        is_private = 1 if (metadata.privacy_status or "private").lower() == "private" else 0
        payload: dict = {
            "access_token": upload_token,
            "v": VK_API_VERSION,
            "group_id": group_id,
            "name": metadata.title[:128],
            "description": (metadata.description or "")[:5000],
            "wallpost": 1,
            "is_private": is_private,
        }

        log.info(
            "VK video.save: group_id=%s, token_type=%s",
            group_id,
            "community" if self.settings.VK_COMMUNITY_TOKEN else "service_key",
        )

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(f"{VK_API_BASE}/video.save", data=payload)
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            err = data["error"]
            code = err.get("error_code", 0)
            msg = err.get("error_msg", "VK video.save failed")
            log.warning("VK video.save error (code=%s): %s", code, msg)
            raise ValueError(f"VK: {msg}")

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
        token = self.settings.VK_COMMUNITY_TOKEN or self.settings.VK_SERVICE_KEY or access_token
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(
                f"{VK_API_BASE}/video.get",
                params={
                    "access_token": token,
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

    async def fetch_video_stats(
        self,
        access_token: str,
        video_id: str,
    ) -> dict:
        """Fetch video statistics via video.get."""
        token = self.settings.VK_COMMUNITY_TOKEN or self.settings.VK_SERVICE_KEY or access_token
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(
                f"{VK_API_BASE}/video.get",
                params={
                    "access_token": token,
                    "v": VK_API_VERSION,
                    "videos": video_id,
                },
            )
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            return {"views": 0, "clicks": 0}
        items = data.get("response", {}).get("items", [])
        if not items:
            return {"views": 0, "clicks": 0}
        item = items[0]
        views = item.get("views", 0)
        likes = item.get("likes", {}).get("count", 0)
        comments = item.get("comments", 0)
        return {
            "views": views,
            "clicks": likes + comments,
        }
