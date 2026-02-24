"""Publication router."""

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.rate_limit import limiter
from app.dependencies import get_publication_service
from app.schemas.publish import PublishRequest, PublishResponse, PublishStatusResponse
from app.services.publication_service import PublicationService

router = APIRouter(prefix="/publish", tags=["publish"])

PUBLISH_RATE_LIMIT = "5/minute"


@router.post("/{content_id}", response_model=PublishResponse)
@limiter.limit(PUBLISH_RATE_LIMIT)
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
        raise HTTPException(status_code=400, detail=str(e))
    # Commit immediately so status polls see the entry while background upload runs
    await db.commit()
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
