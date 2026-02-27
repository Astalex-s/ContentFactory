"""Local filesystem storage for media files (dev)."""

from __future__ import annotations

import asyncio
import logging
import uuid
from pathlib import Path

from app.core.config import get_settings

log = logging.getLogger(__name__)


class LocalFileStorage:
    """Local filesystem storage with path traversal protection."""

    def __init__(self, base_path: str | None = None) -> None:
        settings = get_settings()
        self._base = Path(base_path or settings.MEDIA_BASE_PATH).resolve()

    def _resolve_key(self, key: str) -> Path:
        """Resolve key to full path. Raises ValueError if path traversal detected."""
        # Нормализуем ключ: убираем ведущие слэши, заменяем обратные
        normalized = key.replace("\\", "/").lstrip("/")
        full = (self._base / normalized).resolve()
        if not str(full).startswith(str(self._base)):
            raise ValueError(f"Path traversal detected: {key}")
        return full

    async def upload(self, key: str, data: bytes, content_type: str) -> str:
        """Upload data to local filesystem. Returns the storage key."""
        full = self._resolve_key(key)
        full.parent.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread(full.write_bytes, data)
        return key

    async def download(self, key: str) -> bytes:
        """Download file. Raises FileNotFoundError if not exists."""
        full = self._resolve_key(key)
        if not full.exists() or not full.is_file():
            raise FileNotFoundError(f"File not found: {key}")
        return await asyncio.to_thread(full.read_bytes)

    async def get_url(self, key: str) -> str:
        """Return relative path for serving via FastAPI (/media/...)."""
        normalized = key.replace("\\", "/").lstrip("/")
        return f"/media/{normalized}"

    async def delete(self, key: str) -> None:
        """Delete file. No-op if not exists."""
        full = self._resolve_key(key)
        if full.exists() and full.is_file():
            try:
                await asyncio.to_thread(full.unlink)
            except OSError as e:
                log.warning("Failed to delete %s: %s", key, e)

    async def exists(self, key: str) -> bool:
        """Check if file exists."""
        full = self._resolve_key(key)
        return full.exists() and full.is_file()

    def get_full_path(self, key: str) -> Path:
        """Get full filesystem path (for backward compat with FileResponse)."""
        return self._resolve_key(key)


def build_image_key(product_id: str, ext: str = "png") -> str:
    """Build storage key for product image."""
    return f"images/{product_id}/{uuid.uuid4().hex}.{ext}"


def build_video_key(product_id: str, ext: str = "mp4") -> str:
    """Build storage key for product video."""
    return f"videos/{product_id}/{uuid.uuid4().hex}.{ext}"
