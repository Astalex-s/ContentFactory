"""Storage factory: returns LocalFileStorage or S3Storage by STORAGE_BACKEND."""

from __future__ import annotations

from app.core.config import get_settings
from app.interfaces.storage import StorageInterface
from app.services.media.local_storage import LocalFileStorage
from app.services.media.s3_storage import S3Storage


def get_storage() -> StorageInterface:
    """Return storage implementation based on STORAGE_BACKEND env."""
    backend = get_settings().STORAGE_BACKEND.strip().lower()
    if backend == "s3":
        return S3Storage()
    return LocalFileStorage()
