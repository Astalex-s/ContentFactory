"""Publication service: schedule, process, status sync."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID

from fastapi import BackgroundTasks

from app.core.config import get_settings
from app.core.encryption import decrypt_token
from app.models.publication_queue import PublicationStatus
from app.models.social_account import SocialPlatform
from app.repositories.generated_content import GeneratedContentRepository
from app.repositories.product import ProductRepository
from app.repositories.publication_queue import PublicationQueueRepository
from app.repositories.social_account import SocialAccountRepository
from app.services.social.base_provider import VideoUploadMetadata
from app.services.social.oauth_service import OAuthService
from app.services.social.social_factory import get_provider

log = logging.getLogger(__name__)


class PublicationService:
    """Schedule and process video publications. MVP: BackgroundTasks."""

    def __init__(
        self,
        pub_repo: PublicationQueueRepository,
        content_repo: GeneratedContentRepository,
        account_repo: SocialAccountRepository,
        product_repo: ProductRepository,
        oauth_service: OAuthService | None = None,
    ):
        self.pub_repo = pub_repo
        self.content_repo = content_repo
        self.account_repo = account_repo
        self.product_repo = product_repo
        self.oauth_service = oauth_service
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
    ) -> "PublicationQueue":
        """Add to queue. If scheduled_at is now or past, trigger process via BackgroundTasks."""
        from app.models.publication_queue import PublicationQueue

        content = await self.content_repo.get_by_id(content_id)
        if not content:
            raise ValueError("Контент не найден")

        account = await self.account_repo.get_by_id(account_id)
        if not account:
            raise ValueError("Аккаунт не подключён. Сначала подключите платформу.")
        if account.platform.value != platform.lower():
            raise ValueError("Платформа аккаунта не совпадает с выбранной")

        when = scheduled_at or datetime.now(timezone.utc)
        platform_lower = platform.lower()
        entry = await self.pub_repo.create(
            content_id=content_id,
            platform=platform_lower,
            account_id=account_id,
            scheduled_at=when,
            title=title,
            description=description,
        )
        if background_tasks and when <= datetime.now(timezone.utc):
            background_tasks.add_task(self._process_one, str(entry.id))
        return entry

    async def process_publication(self, queue_id: UUID) -> bool:
        """Process single publication. Returns True if processed."""
        entry = await self.pub_repo.get_by_id(queue_id)
        if not entry or entry.status != PublicationStatus.PENDING:
            return False

        await self.pub_repo.update_status(queue_id, PublicationStatus.PROCESSING)

        try:
            content = await self.content_repo.get_by_id(entry.content_id)
            if not content or not content.file_path:
                await self.pub_repo.update_status(
                    queue_id,
                    PublicationStatus.FAILED,
                    error_message="Content or file not found",
                )
                return False

            # Resolve full path: file_path is relative to MEDIA_BASE_PATH
            base = Path(self.settings.MEDIA_BASE_PATH)
            file_path = str(base / content.file_path)
            if not Path(file_path).exists():
                await self.pub_repo.update_status(
                    queue_id,
                    PublicationStatus.FAILED,
                    error_message="Video file not found on disk",
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
                now = datetime.now(timezone.utc)
                if account.expires_at and account.expires_at <= now + timedelta(minutes=5):
                    try:
                        account = await self.oauth_service.refresh_token(account.id)
                    except Exception as e:
                        log.warning("Token refresh failed, using existing: %s", e)

            platform_enum = SocialPlatform(entry.platform.lower())
            provider = get_provider(platform_enum)

            access_token = decrypt_token(
                account.access_token,
                self.settings.OAUTH_SECRET_KEY,
            )
            if not access_token:
                await self.pub_repo.update_status(
                    queue_id,
                    PublicationStatus.FAILED,
                    error_message="Failed to decrypt token",
                )
                return False

            video_title = entry.title or content.content_text or "Видео"
            video_description = entry.description or content.content_text or ""

            product = await self.product_repo.get_by_id(content.product_id)
            if product and product.marketplace_url:
                link_line = f"\n\nКупить: {product.marketplace_url}"
                video_description = (video_description or "").rstrip() + link_line

            metadata = VideoUploadMetadata(
                title=video_title,
                description=video_description,
                tags=[],
                privacy_status="private",
            )

            result = await provider.upload_video(
                access_token=access_token,
                file_path=file_path,
                metadata=metadata,
            )

            await self.pub_repo.update_status(
                queue_id,
                PublicationStatus.PUBLISHED,
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

    async def _process_one(self, queue_id_str: str) -> None:
        """Background task: process one publication."""
        try:
            queue_id = UUID(queue_id_str)
            await self.process_publication(queue_id)
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
