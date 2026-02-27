"""Media storage service for generated images and videos."""

from __future__ import annotations

import logging
import uuid
from pathlib import Path
from uuid import UUID

from app.core.config import get_settings

log = logging.getLogger(__name__)


class MediaStorageService:
    """Service for storing and retrieving generated media files."""

    def __init__(self, base_path: str | None = None):
        self.base_path = Path(base_path or get_settings().MEDIA_BASE_PATH)

    def _ensure_dir(self, path: Path) -> None:
        path.mkdir(parents=True, exist_ok=True)

    def _product_images_dir(self, product_id: UUID) -> Path:
        return self.base_path / "images" / str(product_id)

    def _product_videos_dir(self, product_id: UUID) -> Path:
        return self.base_path / "videos" / str(product_id)

    def save_image(self, product_id: UUID, data: bytes, ext: str = "png") -> str:
        """Save image data and return relative path."""
        dir_path = self._product_images_dir(product_id)
        self._ensure_dir(dir_path)
        filename = f"{uuid.uuid4().hex}.{ext}"
        file_path = dir_path / filename
        file_path.write_bytes(data)
        return f"images/{product_id}/{filename}"

    def save_video(self, product_id: UUID, data: bytes, ext: str = "mp4") -> str:
        """Save video data and return relative path."""
        dir_path = self._product_videos_dir(product_id)
        self._ensure_dir(dir_path)
        filename = f"{uuid.uuid4().hex}.{ext}"
        file_path = dir_path / filename
        file_path.write_bytes(data)
        return f"videos/{product_id}/{filename}"

    def get_full_path(self, relative_path: str) -> Path:
        """Get full filesystem path from relative path."""
        return self.base_path / relative_path

    def read_file(self, relative_path: str) -> bytes | None:
        """Read file by relative path. Returns None if not found."""
        full = self.get_full_path(relative_path)
        if not full.exists() or not full.is_file():
            return None
        try:
            return full.read_bytes()
        except OSError as e:
            log.warning("Failed to read %s: %s", relative_path, e)
            return None

    def delete_file(self, relative_path: str) -> bool:
        """Delete file by relative path. Returns True if deleted."""
        full = self.get_full_path(relative_path)
        if not full.exists() or not full.is_file():
            return False
        try:
            full.unlink()
            return True
        except OSError as e:
            log.warning("Failed to delete %s: %s", relative_path, e)
            return False
