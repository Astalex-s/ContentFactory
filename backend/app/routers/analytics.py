"""Analytics router."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.config import get_settings
from app.core.encryption import decrypt_token
from app.dependencies import (
    get_analytics_service,
    get_content_service,
    get_oauth_service,
    get_publication_queue_repository,
    get_recommendation_service,
    get_social_account_repository,
)
from app.models.social_account import SocialPlatform
from app.repositories.publication_queue import PublicationQueueRepository
from app.repositories.social_account import SocialAccountRepository
from app.schemas.analytics import (
    AggregatedStatsResponse,
    ContentMetricsResponse,
    ContentRecommendationResponse,
    PublishTimeRecommendationResponse,
    RecordMetricsRequest,
    TopContentResponse,
)
from app.services.analytics_service import AnalyticsService
from app.services.recommendation_service import RecommendationService
from app.services.social.oauth_service import OAuthService
from app.services.social.social_factory import get_provider

log = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.post("/metrics", response_model=ContentMetricsResponse)
async def record_metrics(
    body: RecordMetricsRequest,
    service: AnalyticsService = Depends(get_analytics_service),
) -> ContentMetricsResponse:
    """Record or update content metrics."""
    try:
        metrics = await service.record_metrics(
            content_id=body.content_id,
            platform=body.platform,
            views=body.views,
            clicks=body.clicks,
            marketplace_clicks=body.marketplace_clicks,
            recorded_at=body.recorded_at,
        )
        return ContentMetricsResponse(**metrics)
    except Exception as e:
        log.error("Failed to record metrics: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/metrics/{content_id}", response_model=list[ContentMetricsResponse])
async def get_content_metrics(
    content_id: UUID,
    service: AnalyticsService = Depends(get_analytics_service),
) -> list[ContentMetricsResponse]:
    """Get all metrics for a content."""
    try:
        metrics_list = await service.get_content_metrics(content_id)
        return [ContentMetricsResponse(**m) for m in metrics_list]
    except Exception as e:
        log.error("Failed to get content metrics: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/metrics/{content_id}/latest", response_model=ContentMetricsResponse)
async def get_latest_metrics(
    content_id: UUID,
    service: AnalyticsService = Depends(get_analytics_service),
) -> ContentMetricsResponse:
    """Get latest metrics for a content."""
    try:
        metrics = await service.get_latest_metrics(content_id)
        if not metrics:
            raise HTTPException(status_code=404, detail="Metrics not found")
        return ContentMetricsResponse(**metrics)
    except HTTPException:
        raise
    except Exception as e:
        log.error("Failed to get latest metrics: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/top-content", response_model=list[TopContentResponse])
async def get_top_content(
    limit: int = Query(10, ge=1, le=50),
    platform: str | None = Query(None),
    service: AnalyticsService = Depends(get_analytics_service),
    content_service=Depends(get_content_service),
    pub_repo: PublicationQueueRepository = Depends(get_publication_queue_repository),
) -> list[TopContentResponse]:
    """Get top performing content with preview info (file_path, platform_video_id)."""
    try:
        top_list = await service.get_top_content(limit=limit, platform=platform)
        content_ids = [UUID(cid) for cid in {item["content_id"] for item in top_list}]
        content_map = await content_service.get_by_ids(content_ids)
        pairs = [(UUID(item["content_id"]), item["platform"]) for item in top_list]
        video_ids_map = await pub_repo.get_platform_video_ids(pairs)
        result = []
        for item in top_list:
            c = content_map.get(UUID(item["content_id"]))
            key = (UUID(item["content_id"]), item["platform"])
            platform_video_id = video_ids_map.get(key)
            result.append(
                TopContentResponse(
                    **item,
                    content_file_path=c.file_path if c else None,
                    content_type=c.content_type.value if c and c.content_type else None,
                    platform_video_id=platform_video_id,
                )
            )
        return result
    except Exception as e:
        log.error("Failed to get top content: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/stats", response_model=AggregatedStatsResponse)
async def get_aggregated_stats(
    platform: str | None = Query(None),
    service: AnalyticsService = Depends(get_analytics_service),
) -> AggregatedStatsResponse:
    """Get aggregated statistics."""
    try:
        stats = await service.get_aggregated_stats(platform=platform)
        return AggregatedStatsResponse(**stats)
    except Exception as e:
        log.error("Failed to get aggregated stats: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/refresh-stats")
async def refresh_stats(
    platform: str | None = Query(None, description="Filter by platform (youtube, vk)"),
    service: AnalyticsService = Depends(get_analytics_service),
    account_repo: SocialAccountRepository = Depends(get_social_account_repository),
    pub_repo: PublicationQueueRepository = Depends(get_publication_queue_repository),
    oauth_service: OAuthService = Depends(get_oauth_service),
) -> dict:
    """Bulk refresh stats for all published/processing videos with platform_video_id."""
    settings = get_settings()
    entries = await pub_repo.get_published_with_video_id(platform=platform, limit=500)
    refreshed = 0
    failed = 0
    errors: list[str] = []

    for entry in entries:
        if entry.platform.lower() == "tiktok":
            continue
        video_id = entry.platform_video_id
        if not video_id:
            continue
        try:
            account = await account_repo.get_by_id(entry.account_id)
            if not account:
                errors.append(f"Account {entry.account_id} not found")
                failed += 1
                continue

            if account.refresh_token and account.expires_at:
                now = datetime.now(UTC)
                if account.expires_at <= now + timedelta(minutes=5):
                    try:
                        account = await oauth_service.refresh_token(account.id)
                    except Exception as e:
                        log.warning("Token refresh failed for stats: %s", e)

            access_token = decrypt_token(
                account.access_token,
                settings.OAUTH_SECRET_KEY,
                settings.OAUTH_ENCRYPTION_SALT,
            )
            if not access_token:
                errors.append(f"Failed to decrypt token for account {entry.account_id}")
                failed += 1
                continue

            platform_enum = SocialPlatform(entry.platform.lower())
            provider = get_provider(platform_enum)
            stats = await provider.fetch_video_stats(
                access_token=access_token,
                video_id=video_id,
            )
            await service.record_metrics(
                content_id=entry.content_id,
                platform=entry.platform.lower(),
                views=stats.get("views", 0),
                clicks=stats.get("clicks", 0),
                marketplace_clicks=0,
            )
            refreshed += 1
        except NotImplementedError:
            failed += 1
        except Exception as e:
            log.warning(
                "Refresh stats failed for %s/%s: %s",
                entry.content_id,
                entry.platform,
                e,
            )
            failed += 1
            errors.append(f"{entry.content_id}: {str(e)[:80]}")

    return {"refreshed": refreshed, "failed": failed, "errors": errors[:20]}


@router.post("/fetch/{content_id}/{platform}")
async def fetch_and_record_stats(
    content_id: UUID,
    platform: str,
    account_id: UUID = Query(..., description="Social account ID"),
    video_id: str = Query(..., description="Platform video ID (e.g. YouTube video ID)"),
    service: AnalyticsService = Depends(get_analytics_service),
    account_repo: SocialAccountRepository = Depends(get_social_account_repository),
    oauth_service: OAuthService = Depends(get_oauth_service),
) -> dict:
    """Fetch stats from platform API and record them."""
    try:
        account = await account_repo.get_by_id(account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Social account not found")

        settings = get_settings()
        platform_enum = SocialPlatform(platform.lower())

        # Refresh token if expired (YouTube tokens ~1h)
        if account.refresh_token and account.expires_at:
            now = datetime.now(UTC)
            if account.expires_at <= now + timedelta(minutes=5):
                try:
                    account = await oauth_service.refresh_token(account.id)
                except Exception as e:
                    log.warning("Token refresh failed for stats fetch: %s", e)

        access_token = decrypt_token(
            account.access_token,
            settings.OAUTH_SECRET_KEY,
            settings.OAUTH_ENCRYPTION_SALT,
        )
        if not access_token:
            raise HTTPException(
                status_code=400,
                detail="Не удалось расшифровать токен. Переподключите аккаунт.",
            )

        provider = get_provider(platform_enum)
        stats = await provider.fetch_video_stats(
            access_token=access_token,
            video_id=video_id,
        )

        metrics = await service.record_metrics(
            content_id=content_id,
            platform=platform.lower(),
            views=stats.get("views", 0),
            clicks=stats.get("clicks", 0),
            marketplace_clicks=0,
        )

        return {"success": True, "metrics": metrics}
    except HTTPException:
        raise
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e)) from e
    except Exception as e:
        log.error("Failed to fetch and record stats: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post(
    "/recommendations/content/{content_id}",
    response_model=ContentRecommendationResponse,
)
async def get_content_recommendations(
    content_id: UUID,
    service: RecommendationService = Depends(get_recommendation_service),
) -> ContentRecommendationResponse:
    """Get AI recommendations for content optimization."""
    try:
        result = await service.get_content_recommendations(content_id)
        return ContentRecommendationResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        log.error("Failed to get content recommendations: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get(
    "/recommendations/publish-time",
    response_model=PublishTimeRecommendationResponse,
)
async def get_publish_time_recommendations(
    platform: str = Query(...),
    category: str | None = Query(None),
    service: RecommendationService = Depends(get_recommendation_service),
) -> PublishTimeRecommendationResponse:
    """Get AI recommendations for publish time."""
    try:
        result = await service.get_publish_time_recommendations(platform, category)
        return PublishTimeRecommendationResponse(**result)
    except Exception as e:
        log.error("Failed to get publish time recommendations: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e
