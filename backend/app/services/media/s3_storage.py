"""S3 storage implementation for media files."""

from __future__ import annotations

import logging
from typing import Any

import aioboto3
from botocore.exceptions import ClientError

from app.core.config import get_settings

log = logging.getLogger(__name__)


class S3Storage:
    """S3-compatible storage backend (AWS S3, MinIO, DigitalOcean Spaces)."""

    def __init__(
        self,
        *,
        bucket: str | None = None,
        region: str | None = None,
        endpoint_url: str | None = None,
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
        public_url: str | None = None,
        presigned_expire: int | None = None,
    ) -> None:
        settings = get_settings()
        self.bucket = bucket or settings.S3_BUCKET
        self.region = region or settings.S3_REGION
        raw = endpoint_url or settings.S3_ENDPOINT_URL or None
        self.endpoint_url = self._normalize_endpoint(raw) if raw else None
        self.access_key_id = access_key_id or settings.S3_ACCESS_KEY_ID
        self.secret_access_key = secret_access_key or settings.S3_SECRET_ACCESS_KEY
        self.public_url = public_url or settings.S3_PUBLIC_URL or None
        self.presigned_expire = presigned_expire or settings.S3_PRESIGNED_EXPIRE

    @staticmethod
    def _normalize_endpoint(url: str) -> str:
        """Ensure endpoint has scheme (https://). aiobotocore requires full URL."""
        url = url.strip()
        if not url.startswith(("http://", "https://")):
            return f"https://{url}"
        return url

    def _get_client_kwargs(self) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "region_name": self.region,
            "aws_access_key_id": self.access_key_id,
            "aws_secret_access_key": self.secret_access_key,
        }
        if self.endpoint_url:
            kwargs["endpoint_url"] = self.endpoint_url
        return kwargs

    async def upload(self, key: str, data: bytes, content_type: str) -> str:
        """Upload data to S3. Returns the storage key."""
        try:
            session = aioboto3.Session()
            async with session.client("s3", **self._get_client_kwargs()) as client:  # type: ignore
                await client.put_object(
                    Bucket=self.bucket,
                    Key=key,
                    Body=data,
                    ContentType=content_type,
                )
            return key
        except ClientError as e:
            log.exception("S3 upload failed for key %s: %s", key, e)
            raise
        except Exception as e:
            log.exception("S3 upload error for key %s: %s", key, e)
            raise

    async def download(self, key: str) -> bytes:
        """Download file from S3. Raises FileNotFoundError if not exists."""
        try:
            session = aioboto3.Session()
            async with session.client("s3", **self._get_client_kwargs()) as client:  # type: ignore
                response = await client.get_object(Bucket=self.bucket, Key=key)
                async with response["Body"] as stream:  # type: ignore
                    return await stream.read()
        except ClientError as e:
            if e.response.get("Error", {}).get("Code") == "NoSuchKey":
                raise FileNotFoundError(f"Object not found: {key}") from e
            log.exception("S3 download failed for key %s: %s", key, e)
            raise
        except Exception as e:
            log.exception("S3 download error for key %s: %s", key, e)
            raise

    async def get_url(self, key: str) -> str:
        """Get URL: public URL if S3_PUBLIC_URL set, else presigned URL."""
        if self.public_url:
            base = self.public_url.rstrip("/")
            return f"{base}/{key}" if not key.startswith("/") else f"{base}{key}"

        try:
            session = aioboto3.Session()
            async with session.client("s3", **self._get_client_kwargs()) as client:  # type: ignore
                url = await client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": self.bucket, "Key": key},
                    ExpiresIn=self.presigned_expire,
                )
                return url or ""
        except ClientError as e:
            log.exception("S3 presigned URL failed for key %s: %s", key, e)
            raise
        except Exception as e:
            log.exception("S3 presigned URL error for key %s: %s", key, e)
            raise

    async def delete(self, key: str) -> None:
        """Delete object from S3. No-op if not exists."""
        try:
            session = aioboto3.Session()
            async with session.client("s3", **self._get_client_kwargs()) as client:  # type: ignore
                await client.delete_object(Bucket=self.bucket, Key=key)
        except ClientError as e:
            log.warning("S3 delete failed for key %s: %s", key, e)
        except Exception as e:
            log.warning("S3 delete error for key %s: %s", key, e)

    async def exists(self, key: str) -> bool:
        """Check if object exists in S3."""
        try:
            session = aioboto3.Session()
            async with session.client("s3", **self._get_client_kwargs()) as client:  # type: ignore
                await client.head_object(Bucket=self.bucket, Key=key)
                return True
        except ClientError as e:
            if e.response.get("Error", {}).get("Code") == "404":
                return False
            log.warning("S3 head_object failed for key %s: %s", key, e)
            return False
        except Exception as e:
            log.warning("S3 exists check error for key %s: %s", key, e)
            return False
