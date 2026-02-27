"""Storage interface for media files (images, videos)."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class StorageInterface(Protocol):
    """Protocol for media storage backends (local FS, S3)."""

    async def upload(self, key: str, data: bytes, content_type: str) -> str:
        """
        Upload data to storage.
        Returns the storage key (path) for the uploaded file.
        """
        ...

    async def download(self, key: str) -> bytes:
        """Download file by key. Raises FileNotFoundError if not exists."""
        ...

    async def get_url(self, key: str) -> str:
        """Get URL for accessing the file (public URL or presigned)."""
        ...

    async def delete(self, key: str) -> None:
        """Delete file by key. No-op if not exists."""
        ...

    async def exists(self, key: str) -> bool:
        """Check if file exists by key."""
        ...
