"""YouTube Data API v3 provider for video upload."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from app.core.config import get_settings
from app.services.social.base_provider import (
    BaseSocialProvider,
    VideoUploadMetadata,
    VideoUploadResult,
)

log = logging.getLogger(__name__)


class YouTubeProvider(BaseSocialProvider):
    """YouTube provider using google-api-python-client. videos.insert, OAuth scope."""

    def __init__(self):
        self.settings = get_settings()
        self._timeout = self.settings.SOCIAL_TIMEOUT

    async def upload_video(
        self,
        access_token: str,
        file_path: str,
        metadata: VideoUploadMetadata,
    ) -> VideoUploadResult:
        """Upload video via YouTube Data API v3 videos.insert."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Video file not found: {file_path}")

        def _sync_upload() -> dict:
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaFileUpload

            creds = Credentials(token=access_token)
            youtube = build(
                "youtube",
                "v3",
                credentials=creds,
                cache_discovery=False,
            )
            body = {
                "snippet": {
                    "title": metadata.title[:100],
                    "description": (metadata.description or "")[:5000],
                    "tags": metadata.tags[:500] if metadata.tags else [],
                    "categoryId": "22",
                },
                "status": {
                    "privacyStatus": metadata.privacy_status or "private",
                },
            }
            media = MediaFileUpload(
                str(path),
                mimetype="video/mp4",
                resumable=True,
                chunksize=1024 * 1024,
            )
            request = youtube.videos().insert(
                part="snippet,status",
                body=body,
                media_body=media,
            )
            response = None
            retries = 3
            for attempt in range(retries):
                try:
                    response = request.execute()
                    break
                except Exception as e:
                    err_str = str(e).lower()
                    if "500" in err_str or "503" in err_str:
                        if attempt < retries - 1:
                            import time

                            time.sleep(2**attempt)
                            continue
                    log.error("YouTube upload error: %s", e)
                    raise
            if not response:
                raise RuntimeError("YouTube upload failed")
            video_id = response.get("id", "")
            snippet = response.get("snippet", {})
            status = response.get("status", {})
            published_at = snippet.get("publishedAt") or status.get("publishAt", "")
            upload_status = status.get("uploadStatus", "uploaded")
            return {
                "video_id": video_id,
                "status": upload_status,
                "published_at": published_at,
                "platform_url": f"https://www.youtube.com/watch?v={video_id}" if video_id else None,
            }

        # Upload can take several minutes for larger videos
        upload_timeout = max(self._timeout, 300)
        loop = asyncio.get_event_loop()
        result = await asyncio.wait_for(
            loop.run_in_executor(None, _sync_upload),
            timeout=upload_timeout,
        )
        return VideoUploadResult(
            video_id=result["video_id"],
            status=result["status"],
            published_at=result.get("published_at"),
            platform_url=result.get("platform_url"),
        )

    async def check_video_status(
        self,
        access_token: str,
        video_id: str,
    ) -> str:
        """Check video status via videos.list."""
        def _sync_check() -> str:
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build

            creds = Credentials(token=access_token)
            youtube = build(
                "youtube",
                "v3",
                credentials=creds,
                cache_discovery=False,
            )
            resp = youtube.videos().list(
                part="status,processingDetails",
                id=video_id,
            ).execute()
            items = resp.get("items", [])
            if not items:
                return "unknown"
            item = items[0]
            status = item.get("status", {})
            upload_status = status.get("uploadStatus", "unknown")
            proc = item.get("processingDetails", {})
            proc_status = proc.get("processingStatus", "")
            if proc_status:
                return proc_status
            return upload_status

        loop = asyncio.get_event_loop()
        return await asyncio.wait_for(
            loop.run_in_executor(None, _sync_check),
            timeout=self._timeout,
        )
