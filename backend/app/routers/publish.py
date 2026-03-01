"""Publication router."""

import logging
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.publish_rate_limit import is_publish_rate_limit_enabled
from app.core.rate_limit import limiter
from app.dependencies import get_content_service, get_publication_service
from app.models.publication_queue import PublicationStatus
from app.repositories.app_settings import AppSettingsRepository
from app.repositories.generated_content import GeneratedContentRepository
from app.repositories.publication_queue import PublicationQueueRepository
from app.repositories.social_account import SocialAccountRepository
from app.schemas.publish import (
    BulkPublishRequest,
    BulkPublishResponse,
    PublicationListResponse,
    PublishRequest,
    PublishResponse,
    PublishStatusResponse,
)
from app.services.publication_service import PublicationService

log = logging.getLogger(__name__)
router = APIRouter(prefix="/publish", tags=["publish"])

PUBLISH_RATE_LIMIT = "5/minute"
BULK_PUBLISH_RATE_LIMIT = "3/minute"


@router.post("/{content_id}", response_model=PublishResponse)
@limiter.limit(PUBLISH_RATE_LIMIT, exempt_when=lambda req=None: not is_publish_rate_limit_enabled())
async def schedule_publication(
    request: Request,
    content_id: UUID,
    body: PublishRequest,
    background_tasks: BackgroundTasks,
    service: PublicationService = Depends(get_publication_service),
    db: AsyncSession = Depends(get_db),
) -> PublishResponse:
    """
    Schedule publication. Body: platform, account_id, scheduled_at (optional).
    404 if content not found. 400 if platform not connected.
    """
    try:
        entry = await service.schedule_publication(
            content_id=content_id,
            platform=body.platform,
            account_id=body.account_id,
            scheduled_at=body.scheduled_at,
            background_tasks=background_tasks,
            title=body.title,
            description=body.description,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except IntegrityError as e:
        await db.rollback()
        log.warning("Publication integrity error (content/account FK?): %s", e)
        raise HTTPException(
            status_code=400,
            detail="Контент или аккаунт не найден. Обновите страницу.",
        ) from e
    except Exception as e:
        await db.rollback()
        log.exception("Publication schedule failed: %s", e)
        raise HTTPException(
            status_code=500,
            detail="Ошибка при планировании публикации. Попробуйте позже.",
        ) from e
    try:
        await db.commit()
    except IntegrityError as e:
        await db.rollback()
        log.warning("Publication commit integrity error: %s", e)
        raise HTTPException(
            status_code=400,
            detail="Контент или аккаунт не найден. Обновите страницу.",
        ) from e
    return PublishResponse(
        id=entry.id,
        content_id=entry.content_id,
        platform=entry.platform,
        account_id=entry.account_id,
        scheduled_at=entry.scheduled_at,
        status=entry.status.value,
        error_message=entry.error_message,
        platform_video_id=entry.platform_video_id,
        created_at=entry.created_at,
    )


@router.get("/status/{id}", response_model=PublishStatusResponse)
async def get_publication_status(
    id: UUID,
    service: PublicationService = Depends(get_publication_service),
) -> PublishStatusResponse:
    """Get publication status by queue ID. 404 if not found."""
    entry = await service.get_status(id)
    if not entry:
        raise HTTPException(status_code=404, detail="Публикация не найдена")
    return PublishStatusResponse(
        id=entry.id,
        status=entry.status.value,
        error_message=entry.error_message,
        platform_video_id=entry.platform_video_id,
    )


@router.get("/", response_model=PublicationListResponse)
async def get_publications(
    status: str | None = Query(None, pattern="^(pending|processing|published|failed)$"),
    platform: str | None = Query(None, pattern="^(youtube|vk|tiktok)$"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: PublicationService = Depends(get_publication_service),
    content_service=Depends(get_content_service),
) -> PublicationListResponse:
    """Get list of publications with optional filters. Includes content preview info."""
    status_enum = PublicationStatus(status) if status else None

    items = await service.get_publications(
        status=status_enum,
        platform=platform,
        limit=limit,
        offset=offset,
    )

    total = await service.count_publications(
        status=status_enum,
        platform=platform,
    )

    content_ids = [item.content_id for item in items]
    content_map = await content_service.get_by_ids(content_ids)

    return PublicationListResponse(
        total=total,
        items=[
            PublishResponse(
                id=item.id,
                content_id=item.content_id,
                platform=item.platform,
                account_id=item.account_id,
                scheduled_at=item.scheduled_at,
                status=item.status.value,
                error_message=item.error_message,
                platform_video_id=item.platform_video_id,
                created_at=item.created_at,
                content_file_path=((c := content_map.get(item.content_id)) and c.file_path or None),
                content_type=(
                    (c := content_map.get(item.content_id)) and c.content_type.value or None
                ),
            )
            for item in items
        ],
        limit=limit,
        offset=offset,
    )


@router.post("/bulk", response_model=BulkPublishResponse)
@limiter.limit(
    BULK_PUBLISH_RATE_LIMIT, exempt_when=lambda req=None: not is_publish_rate_limit_enabled()
)
async def bulk_schedule_publications(
    request: Request,
    body: BulkPublishRequest,
    background_tasks: BackgroundTasks,
    service: PublicationService = Depends(get_publication_service),
    db: AsyncSession = Depends(get_db),
) -> BulkPublishResponse:
    """Schedule multiple publications at once. Max 50 per request."""
    try:
        entries = await service.bulk_schedule_publications(
            publications=[pub.model_dump() for pub in body.publications],
            background_tasks=background_tasks,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except IntegrityError as e:
        await db.rollback()
        log.warning("Bulk publication integrity error: %s", e)
        raise HTTPException(
            status_code=400,
            detail="Контент или аккаунт не найден. Обновите страницу.",
        ) from e
    except Exception as e:
        await db.rollback()
        log.exception("Bulk publication schedule failed: %s", e)
        raise HTTPException(
            status_code=500,
            detail="Ошибка при планировании публикаций. Попробуйте позже.",
        ) from e
    try:
        await db.commit()
    except IntegrityError as e:
        await db.rollback()
        log.warning("Bulk publication commit integrity error: %s", e)
        raise HTTPException(
            status_code=400,
            detail="Контент или аккаунт не найден. Обновите страницу.",
        ) from e

    return BulkPublishResponse(
        created_count=len(entries),
        publications=[
            PublishResponse(
                id=entry.id,
                content_id=entry.content_id,
                platform=entry.platform,
                account_id=entry.account_id,
                scheduled_at=entry.scheduled_at,
                status=entry.status.value,
                error_message=entry.error_message,
                platform_video_id=entry.platform_video_id,
                created_at=entry.created_at,
            )
            for entry in entries
        ],
    )


@router.post("/auto-publish-check")
async def auto_publish_check(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    service: PublicationService = Depends(get_publication_service),
) -> dict:
    """
    Check and schedule auto-publications. Call from cron every minute.
    Publishes approved video content created 5+ minutes ago.
    """
    settings_repo = AppSettingsRepository(db)
    if await settings_repo.get("auto_publish") != "true":
        return {"scheduled": 0, "message": "auto_publish disabled"}

    content_repo = GeneratedContentRepository(db)
    pub_repo = PublicationQueueRepository(db)
    account_repo = SocialAccountRepository(db)

    candidates = await content_repo.get_ready_for_auto_publish(min_age_minutes=5, limit=20)
    scheduled = 0
    for content in candidates:
        if await pub_repo.has_content_scheduled(content.id):
            continue
        accounts = await account_repo.list_by_platform(content.platform.value)
        if not accounts:
            log.warning(
                "Auto-publish: no account for platform %s, content %s", content.platform, content.id
            )
            continue
        account = accounts[0]
        try:
            entry = await service.schedule_publication(
                content_id=content.id,
                platform=content.platform.value,
                account_id=account.id,
                scheduled_at=None,
                background_tasks=background_tasks,
            )
            scheduled += 1
            log.info("Auto-publish scheduled: content %s -> %s", content.id, entry.id)
        except Exception as e:
            log.warning("Auto-publish failed for content %s: %s", content.id, e)

    await db.commit()
    return {"scheduled": scheduled}


@router.post("/process-pending")
async def process_pending_publications(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    service: PublicationService = Depends(get_publication_service),
) -> dict:
    """
    Process pending publications whose scheduled_at has passed.
    Call from cron every minute (e.g. * * * * * curl -X POST .../publish/process-pending).
    """
    queued = await service.process_pending_publications(
        background_tasks=background_tasks,
        limit=20,
    )
    await db.commit()
    return {"queued": queued}


@router.delete("/{id}")
async def cancel_publication(
    id: UUID,
    service: PublicationService = Depends(get_publication_service),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Cancel/delete a publication. Only pending publications can be cancelled."""
    deleted = await service.cancel_publication(id)
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Публикация не найдена или уже обработана",
        )
    await db.commit()
    return {"message": "Публикация отменена"}
