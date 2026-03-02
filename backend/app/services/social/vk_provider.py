"""VK provider: OAuth2 -> video.save -> upload_url -> POST MP4.

Официальный flow (требует одобрения VK по запросу в поддержку):
1. OAuth2 token (video, wall scopes) через VK ID
2. video.save -> get upload_url (wallpost=1 публикует на стену)
3. POST MP4 to upload_url (multipart)
4. VK processes video (async, polling video.get)
"""

from __future__ import annotations

import asyncio
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
VK_UPLOAD_TIMEOUT = 300.0
VK_POLL_INTERVAL = 5
VK_POLL_MAX_ATTEMPTS = 60  # 5 min max
VK_SAVE_RETRIES = 3


class VKProvider(BaseSocialProvider):
    """VK video upload: только OAuth-токен пользователя (официальный API)."""

    def __init__(self):
        self.settings = get_settings()
        self._timeout = self.settings.SOCIAL_TIMEOUT

    async def upload_video(
        self,
        access_token: str,
        file_path: str,
        metadata: VideoUploadMetadata,
    ) -> VideoUploadResult:
        """1) video.save -> upload_url 2) POST file 3) poll until ready."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Video file not found: {file_path}")

        upload_url = await self._video_save(
            token=access_token,
            group_id=None,
            metadata=metadata,
        )
        if not upload_url:
            raise ValueError(
                "VK: не удалось получить upload_url. "
                "Убедитесь, что приложение VK одобрено для video.save (запрос в поддержку devsupport@corp.vk.com)."
            )

        # POST MP4 to upload_url
        full_id = await self._upload_file(upload_url, path)
        if not full_id:
            raise ValueError("VK: загрузка не вернула video_id")

        # Poll until processing complete (VK processes async)
        full_id = await self._poll_until_ready(access_token, full_id)

        # video.save wallpost=1 уже публикует на стену; wall.post не нужен
        return VideoUploadResult(
            video_id=full_id,
            status="uploaded",
            published_at=None,
            platform_url=f"https://vk.com/video{full_id}" if full_id != "unknown" else None,
        )

    async def _video_save(
        self,
        token: str,
        group_id: str | None,
        metadata: VideoUploadMetadata,
    ) -> str | None:
        """Call video.save, return upload_url or None. Retry on 5xx."""
        is_private = 1 if (metadata.privacy_status or "private").lower() == "private" else 0
        payload: dict = {
            "access_token": token,
            "v": VK_API_VERSION,
            "name": (metadata.title or "Видео")[:128],
            "description": (metadata.description or "")[:5000],
            "wallpost": 1,
            "is_private": is_private,
        }
        if group_id:
            payload["group_id"] = group_id

        for attempt in range(VK_SAVE_RETRIES):
            try:
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
                return data.get("response", {}).get("upload_url")
            except ValueError:
                raise
            except (httpx.HTTPStatusError, httpx.RequestError) as e:
                if attempt < VK_SAVE_RETRIES - 1:
                    log.warning("VK video.save retry %d/%d: %s", attempt + 1, VK_SAVE_RETRIES, e)
                    await asyncio.sleep(2**attempt)
                    continue
                raise

    async def _upload_file(self, upload_url: str, path: Path) -> str:
        """POST video file to upload_url, return owner_id_video_id. Retry on 5xx."""
        for attempt in range(VK_SAVE_RETRIES):
            try:
                with open(path, "rb") as f:
                    files = {"video_file": (path.name, f, "video/mp4")}
                    async with httpx.AsyncClient(
                        timeout=httpx.Timeout(VK_UPLOAD_TIMEOUT)
                    ) as client:
                        upload_resp = await client.post(upload_url, files=files)
                upload_resp.raise_for_status()
                upload_data = upload_resp.json()
                video_id = str(upload_data.get("video_id", ""))
                owner_id = upload_data.get("owner_id", "")
                if owner_id and video_id:
                    return f"{owner_id}_{video_id}"
                return video_id or "unknown"
            except (httpx.HTTPStatusError, httpx.RequestError) as e:
                if attempt < VK_SAVE_RETRIES - 1:
                    log.warning("VK upload retry %d/%d: %s", attempt + 1, VK_SAVE_RETRIES, e)
                    await asyncio.sleep(2**attempt)
                    continue
                raise
        return "unknown"

    async def _poll_until_ready(self, token: str, video_id: str) -> str:
        """Poll video.get until processing=0."""
        for _ in range(VK_POLL_MAX_ATTEMPTS):
            status = await self.check_video_status(token, video_id)
            if status == "available":
                return video_id
            if status == "unknown":
                return video_id
            await asyncio.sleep(VK_POLL_INTERVAL)
        log.warning(
            "VK video %s still processing after %d attempts", video_id, VK_POLL_MAX_ATTEMPTS
        )
        return video_id

    async def check_video_status(
        self,
        access_token: str,
        video_id: str,
    ) -> str:
        """Check video status via video.get."""
        token = (access_token or "").strip()
        if not token:
            return "unknown"
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
        token = (access_token or "").strip()
        if not token:
            return {"views": 0, "clicks": 0}
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
