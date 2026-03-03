"""Publication service: schedule, process, status sync."""

from __future__ import annotations

import logging
import os
import subprocess
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import UUID

from fastapi import BackgroundTasks

from app.core.config import get_settings
from app.core.encryption import decrypt_token
from app.models.generated_content import ContentType
from app.models.publication_queue import PublicationQueue, PublicationStatus
from app.models.social_account import SocialPlatform
from app.repositories.generated_content import GeneratedContentRepository
from app.repositories.product import ProductRepository
from app.repositories.publication_queue import PublicationQueueRepository
from app.repositories.social_account import SocialAccountRepository
from app.services.social.base_provider import VideoUploadMetadata
from app.services.social.oauth_service import OAuthService
from app.services.social.social_factory import get_provider

if TYPE_CHECKING:
    pass

log = logging.getLogger(__name__)

SHORTS_DURATION_THRESHOLD_SEC = 60


def _get_video_duration_sec(file_path: str) -> float | None:
    """Get video duration in seconds via ffprobe. Returns None on error."""
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "csv=p=0",
                file_path,
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return None
        return float(result.stdout.strip())
    except (subprocess.SubprocessError, ValueError):
        return None


class PublicationService:
    """Schedule and process video publications. MVP: BackgroundTasks."""

    def __init__(
        self,
        pub_repo: PublicationQueueRepository,
        content_repo: GeneratedContentRepository,
        account_repo: SocialAccountRepository,
        product_repo: ProductRepository,
        oauth_service: OAuthService | None = None,
        storage=None,
    ):
        self.pub_repo = pub_repo
        self.content_repo = content_repo
        self.account_repo = account_repo
        self.product_repo = product_repo
        self.oauth_service = oauth_service
        self.storage = storage
        self.settings = get_settings()

    async def schedule_publication(
        self,
        content_id: UUID,
        platform: str,
        account_id: UUID,
        scheduled_at: datetime | None = None,
        background_tasks: BackgroundTasks | None = None,
        title: str | None = None,
        description: str | None = None,
        privacy_status: str = "private",
    ) -> PublicationQueue:
        """Add to queue. If scheduled_at is now or past, trigger process via BackgroundTasks."""
        content = await self.content_repo.get_by_id(content_id)
        if not content:
            raise ValueError("Контент не найден")

        account = await self.account_repo.get_by_id(account_id)
        if not account:
            raise ValueError("Аккаунт не подключён. Сначала подключите платформу.")
        if account.platform.value != platform.lower():
            raise ValueError("Платформа аккаунта не совпадает с выбранной")

        when = scheduled_at or datetime.now(UTC)
        platform_lower = platform.lower()
        entry = await self.pub_repo.create(
            content_id=content_id,
            platform=platform_lower,
            account_id=account_id,
            scheduled_at=when,
            title=title,
            description=description,
            privacy_status=privacy_status,
        )
        if background_tasks and when <= datetime.now(UTC):
            background_tasks.add_task(self._process_one, str(entry.id))
        return entry

    async def process_pending_publications(
        self,
        background_tasks: BackgroundTasks,
        limit: int = 20,
    ) -> int:
        """
        Process pending publications whose scheduled_at has passed.
        Call from cron every minute. Returns count of queued for processing.
        """
        pending = await self.pub_repo.get_pending(limit=limit)
        for entry in pending:
            background_tasks.add_task(self._process_one, str(entry.id))
        if pending:
            log.info("Queued %d pending publications for processing", len(pending))
        return len(pending)

    async def process_publication(self, queue_id: UUID) -> bool:
        """Process single publication. Returns True if processed."""
        entry = await self.pub_repo.get_by_id(queue_id)
        if not entry or entry.status != PublicationStatus.PENDING:
            return False

        await self.pub_repo.update_status(queue_id, PublicationStatus.PROCESSING)

        temp_file: Path | None = None
        try:
            content = await self.content_repo.get_by_id(entry.content_id)
            if not content:
                await self.pub_repo.update_status(
                    queue_id,
                    PublicationStatus.FAILED,
                    error_message="Content not found",
                )
                return False

            account = await self.account_repo.get_by_id(entry.account_id)
            if not account:
                await self.pub_repo.update_status(
                    queue_id,
                    PublicationStatus.FAILED,
                    error_message="Account not found",
                )
                return False

            # Refresh token if expired (YouTube tokens ~1h)
            if self.oauth_service and account.refresh_token:
                now = datetime.now(UTC)
                if account.expires_at and account.expires_at <= now + timedelta(minutes=5):
                    try:
                        account = await self.oauth_service.refresh_token(account.id)
                    except Exception as e:
                        log.warning("Token refresh failed, using existing: %s", e)

            access_token = decrypt_token(
                account.access_token,
                self.settings.OAUTH_SECRET_KEY,
                self.settings.OAUTH_ENCRYPTION_SALT,
            )
            if not access_token:
                await self.pub_repo.update_status(
                    queue_id,
                    PublicationStatus.FAILED,
                    error_message="Failed to decrypt token",
                )
                return False

            # Video/image: require file_path
            if not content.file_path:
                await self.pub_repo.update_status(
                    queue_id,
                    PublicationStatus.FAILED,
                    error_message="Content or file not found",
                )
                return False

            # Resolve file path: local FS or download from S3 to temp
            key = content.file_path
            file_path: str | None = None

            if self.storage:
                try:
                    exists = await self.storage.exists(key)
                    if not exists:
                        await self.pub_repo.update_status(
                            queue_id,
                            PublicationStatus.FAILED,
                            error_message="Video file not found in storage",
                        )
                        return False
                    # S3: download to temp file (providers need file path)
                    url = await self.storage.get_url(key)
                    if url.startswith("http"):
                        data = await self.storage.download(key)
                        suffix = Path(key).suffix or ".mp4"
                        fd, path = tempfile.mkstemp(suffix=suffix)
                        Path(path).write_bytes(data)
                        os.close(fd)
                        temp_file = Path(path)
                        file_path = str(temp_file)
                    else:
                        from app.services.media.local_storage import (
                            LocalFileStorage as _LFS,
                        )

                        if isinstance(self.storage, _LFS):
                            file_path = str(self.storage.get_full_path(key))
                except (FileNotFoundError, ValueError) as e:
                    await self.pub_repo.update_status(
                        queue_id,
                        PublicationStatus.FAILED,
                        error_message=f"Storage error: {e}",
                    )
                    return False
            else:
                base = Path(self.settings.MEDIA_BASE_PATH)
                file_path = str(base / key)
                if not Path(file_path).exists():
                    await self.pub_repo.update_status(
                        queue_id,
                        PublicationStatus.FAILED,
                        error_message="Video file not found on disk",
                    )
                    return False

            platform_enum = SocialPlatform(entry.platform.lower())
            provider = get_provider(platform_enum)

            video_title = entry.title or content.content_text or "Видео"
            video_description = entry.description or content.content_text or ""

            # Ссылку в описание добавляем только для длинных видео (≥60 сек).
            # Shorts: ссылка только в QR-коде в конце видео.
            duration_sec = _get_video_duration_sec(file_path) if file_path else None
            if duration_sec is not None and duration_sec >= SHORTS_DURATION_THRESHOLD_SEC:
                product = await self.product_repo.get_by_id(content.product_id)
                if product and product.marketplace_url:
                    url = product.marketplace_url.strip()
                    if url.startswith("http://"):
                        url = "https://" + url[7:]
                    elif not url.startswith("https://"):
                        url = "https://" + url
                    link_block = f"\n\nКупить:\n{url}"
                    video_description = (video_description or "").rstrip() + link_block

            if not file_path:
                await self.pub_repo.update_status(
                    queue_id,
                    PublicationStatus.FAILED,
                    error_message="Could not resolve file path",
                )
                return False

            metadata = VideoUploadMetadata(
                title=video_title,
                description=video_description,
                tags=[],
                privacy_status=entry.privacy_status or "private",
            )

            result = await provider.upload_video(
                access_token=access_token,
                file_path=file_path,
                metadata=metadata,
            )

            # Не помечаем PUBLISHED сразу: YouTube обрабатывает видео асинхронно.
            # Оставляем PROCESSING + platform_video_id — status_sync проверит и отметит
            # PUBLISHED только когда платформа подтвердит готовность (processed/succeeded).
            await self.pub_repo.update_status(
                queue_id,
                PublicationStatus.PROCESSING,
                platform_video_id=result.video_id,
            )
            return True
        except NotImplementedError as e:
            log.warning("Provider not implemented: %s", e)
            await self.pub_repo.update_status(
                queue_id,
                PublicationStatus.FAILED,
                error_message=str(e),
            )
            return False
        except Exception as e:
            log.exception("Publication failed: %s", e)
            await self.pub_repo.update_status(
                queue_id,
                PublicationStatus.FAILED,
                error_message=str(e)[:500],
            )
            return False
        finally:
            if temp_file is not None and temp_file.exists():
                try:
                    temp_file.unlink()
                except OSError:
                    pass

    async def _process_one(self, queue_id_str: str) -> None:
        """Background task: process one publication. Uses fresh DB session."""
        try:
            queue_id = UUID(queue_id_str)
            await run_process_publication_task(queue_id)
        except Exception as e:
            log.exception("Background process_publication failed: %s", e)

    async def update_status(
        self,
        queue_id: UUID,
        status: PublicationStatus,
        error_message: str | None = None,
        platform_video_id: str | None = None,
    ) -> bool:
        """Update publication status."""
        updated = await self.pub_repo.update_status(
            queue_id,
            status,
            error_message=error_message,
            platform_video_id=platform_video_id,
        )
        return updated is not None

    async def get_status(self, queue_id: UUID):
        """Get publication queue entry by ID. Returns None if not found."""
        return await self.pub_repo.get_by_id(queue_id)

    async def get_publications(
        self,
        status: PublicationStatus | None = None,
        platform: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[PublicationQueue]:
        """Get list of publications with filters."""
        return await self.pub_repo.get_all(
            status=status,
            platform=platform,
            limit=limit,
            offset=offset,
        )

    async def count_publications(
        self,
        status: PublicationStatus | None = None,
        platform: str | None = None,
    ) -> int:
        """Count publications with filters."""
        return await self.pub_repo.count_all(status=status, platform=platform)

    async def bulk_schedule_publications(
        self,
        publications: list[dict],
        background_tasks: BackgroundTasks | None = None,
    ) -> list[PublicationQueue]:
        """Schedule multiple publications at once."""
        # Validate all content and accounts exist
        for pub in publications:
            content = await self.content_repo.get_by_id(pub["content_id"])
            if not content:
                raise ValueError(f"Контент {pub['content_id']} не найден")

            account = await self.account_repo.get_by_id(pub["account_id"])
            if not account:
                raise ValueError(f"Аккаунт {pub['account_id']} не подключён")

            if account.platform.value != pub["platform"].lower():
                raise ValueError(
                    f"Платформа аккаунта {account.platform.value} "
                    f"не совпадает с выбранной {pub['platform']}"
                )

        # Create all entries
        entries = await self.pub_repo.bulk_create(publications)

        # Schedule immediate publications
        if background_tasks:
            now = datetime.now(UTC)
            for entry in entries:
                if entry.scheduled_at <= now:
                    background_tasks.add_task(self._process_one, str(entry.id))

        return entries

    async def cancel_publication(self, queue_id: UUID) -> bool:
        """Cancel/delete a publication. Only pending can be cancelled."""
        entry = await self.pub_repo.get_by_id(queue_id)
        if not entry:
            return False

        # Only allow cancelling pending publications
        if entry.status != PublicationStatus.PENDING:
            return False

        return await self.pub_repo.delete(queue_id)


async def run_process_publication_task(queue_id: UUID) -> None:
    """
    Process one publication with a fresh DB session.
    Used by background tasks (cron/process-pending) when request session is closed.
    """
    from app.core.database import async_session_maker
    from app.services.media import get_storage

    async with async_session_maker() as session:
        oauth = OAuthService(session)
        storage = get_storage()
        svc = PublicationService(
            PublicationQueueRepository(session),
            GeneratedContentRepository(session),
            SocialAccountRepository(session),
            ProductRepository(session),
            oauth_service=oauth,
            storage=storage,
        )
        await svc.process_publication(queue_id)
        await session.commit()
