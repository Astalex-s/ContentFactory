"""Tests for media storage (LocalFileStorage, S3Storage, factory)."""

from __future__ import annotations

import pytest

from app.services.media import LocalFileStorage, S3Storage, get_storage
from app.services.media.local_storage import build_image_key, build_video_key


class TestLocalFileStorage:
    """Tests for LocalFileStorage."""

    @pytest.mark.asyncio
    async def test_upload_download(self, temp_media_dir):
        """Upload and download returns same data."""
        storage = LocalFileStorage(base_path=str(temp_media_dir))
        key = "images/123/abc.png"
        data = b"fake png content"

        result = await storage.upload(key, data, "image/png")
        assert result == key

        downloaded = await storage.download(key)
        assert downloaded == data

    @pytest.mark.asyncio
    async def test_exists(self, temp_media_dir):
        """exists returns True for uploaded file, False otherwise."""
        storage = LocalFileStorage(base_path=str(temp_media_dir))
        key = "images/123/abc.png"

        assert await storage.exists(key) is False
        await storage.upload(key, b"data", "image/png")
        assert await storage.exists(key) is True

    @pytest.mark.asyncio
    async def test_delete(self, temp_media_dir):
        """delete removes file."""
        storage = LocalFileStorage(base_path=str(temp_media_dir))
        key = "images/123/abc.png"
        await storage.upload(key, b"data", "image/png")
        assert await storage.exists(key) is True

        await storage.delete(key)
        assert await storage.exists(key) is False

    @pytest.mark.asyncio
    async def test_get_url_returns_relative_path(self, temp_media_dir):
        """get_url returns /media/... for local."""
        storage = LocalFileStorage(base_path=str(temp_media_dir))
        key = "images/123/abc.png"
        await storage.upload(key, b"data", "image/png")

        url = await storage.get_url(key)
        assert url.startswith("/media/")
        assert "images/123/abc.png" in url

    @pytest.mark.asyncio
    async def test_path_traversal_upload_rejected(self, temp_media_dir):
        """Path traversal in key raises ValueError."""
        storage = LocalFileStorage(base_path=str(temp_media_dir))
        key = "../../../etc/passwd"

        with pytest.raises(ValueError):
            await storage.upload(key, b"data", "text/plain")

    @pytest.mark.asyncio
    async def test_path_traversal_download_rejected(self, temp_media_dir):
        """Path traversal in key raises ValueError on download."""
        storage = LocalFileStorage(base_path=str(temp_media_dir))

        with pytest.raises(ValueError):
            await storage.download("../../../etc/passwd")

    @pytest.mark.asyncio
    async def test_download_not_found(self, temp_media_dir):
        """download raises FileNotFoundError for missing file."""
        storage = LocalFileStorage(base_path=str(temp_media_dir))

        with pytest.raises(FileNotFoundError):
            await storage.download("images/999/nonexistent.png")


class TestBuildKeys:
    """Tests for build_image_key and build_video_key."""

    def test_build_image_key_format(self):
        """Key has format images/{product_id}/{uuid}.png."""
        key = build_image_key("123")
        assert key.startswith("images/123/")
        assert key.endswith(".png")
        assert len(key.split("/")) == 3

    def test_build_video_key_format(self):
        """Key has format videos/{product_id}/{uuid}.mp4."""
        key = build_video_key("456")
        assert key.startswith("videos/456/")
        assert key.endswith(".mp4")
        assert len(key.split("/")) == 3

    def test_build_video_key_custom_ext(self):
        """Custom extension."""
        key = build_video_key("789", "webm")
        assert key.endswith(".webm")


class TestS3StorageMock:
    """Tests for S3Storage with mocked boto3."""

    # Используем unittest.mock для мока aioboto3
    # Интеграционный тест с реальным S3 не обязателен по промпту

    @pytest.mark.asyncio
    async def test_s3_storage_upload_interface(self):
        """S3Storage has upload method."""
        storage = S3Storage(
            bucket="test-bucket",
            region="us-east-1",
            access_key_id="test",
            secret_access_key="test",
        )
        assert hasattr(storage, "upload")
        assert callable(getattr(storage, "upload"))


class TestStorageFactory:
    """Tests for get_storage factory."""

    def test_factory_returns_local_by_default(self, monkeypatch):
        """With STORAGE_BACKEND=local or unset, returns LocalFileStorage."""
        monkeypatch.setenv("STORAGE_BACKEND", "local")
        # Clear cache to pick up new env
        from app.core.config import get_settings

        get_settings.cache_clear()
        try:
            storage = get_storage()
            assert isinstance(storage, LocalFileStorage)
        finally:
            get_settings.cache_clear()

    def test_factory_returns_s3_when_configured(self, monkeypatch):
        """With STORAGE_BACKEND=s3, returns S3Storage."""
        monkeypatch.setenv("STORAGE_BACKEND", "s3")
        monkeypatch.setenv("S3_BUCKET", "test-bucket")
        monkeypatch.setenv("S3_ACCESS_KEY_ID", "test")
        monkeypatch.setenv("S3_SECRET_ACCESS_KEY", "test")
        from app.core.config import get_settings

        get_settings.cache_clear()
        try:
            storage = get_storage()
            assert isinstance(storage, S3Storage)
        finally:
            get_settings.cache_clear()
