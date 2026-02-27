"""Status sync: periodic check of publication status via platform APIs.
MVP: BackgroundTasks + asyncio. Interface ready for Celery."""

from __future__ import annotations

import logging

from app.core.config import get_settings
from app.core.encryption import decrypt_token
from app.models.publication_queue import PublicationStatus
from app.repositories.publication_queue import PublicationQueueRepository
from app.repositories.social_account import SocialAccountRepository
from app.services.social.base_provider import BaseSocialProvider
from app.services.social.social_factory import get_provider
from app.models.social_account import SocialPlatform

log = logging.getLogger(__name__)


class StatusSyncService:
    """Sync publication status from platform APIs. MVP: run via BackgroundTasks."""

    def __init__(
        self,
        pub_repo: PublicationQueueRepository,
        account_repo: SocialAccountRepository,
    ):
        self.pub_repo = pub_repo
        self.account_repo = account_repo
        self.settings = get_settings()

    async def sync_pending_processing(self, limit: int = 20) -> int:
        """
        Check status of entries in PROCESSING. Update to PUBLISHED if platform reports done.
        Returns count of updated entries.
        """
        entries = await self.pub_repo.get_processing(limit=limit)
        updated = 0
        for entry in entries:
            if not entry.platform_video_id:
                continue
            try:
                account = await self.account_repo.get_by_id(entry.account_id)
                if not account:
                    continue
                token = decrypt_token(
                    account.access_token,
                    self.settings.OAUTH_SECRET_KEY,
                    self.settings.OAUTH_ENCRYPTION_SALT,
                )
                if not token:
                    continue
                provider: BaseSocialProvider = get_provider(SocialPlatform(entry.platform))
                status = await provider.check_video_status(token, entry.platform_video_id)
                if status in ("processed", "succeeded", "available", "uploaded"):
                    await self.pub_repo.update_status(
                        entry.id,
                        PublicationStatus.PUBLISHED,
                    )
                    updated += 1
            except Exception as e:
                log.warning("Status sync failed for %s: %s", entry.id, e)
        return updated


async def run_status_sync_task() -> None:
    """Background task: run status sync. Call from scheduler or Celery."""
    from app.core.database import async_session_maker

    async with async_session_maker() as session:
        pub_repo = PublicationQueueRepository(session)
        account_repo = SocialAccountRepository(session)
        svc = StatusSyncService(pub_repo, account_repo)
        count = await svc.sync_pending_processing()
        if count:
            log.info("Status sync: updated %d publications", count)
        await session.commit()
