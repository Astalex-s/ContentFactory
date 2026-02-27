"""Analytics router."""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies import (
    get_analytics_service,
    get_recommendation_service,
    get_social_account_repository,
)
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
        raise HTTPException(status_code=500, detail=str(e))


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
        raise HTTPException(status_code=500, detail=str(e))


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
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/top-content", response_model=list[TopContentResponse])
async def get_top_content(
    limit: int = Query(10, ge=1, le=50),
    platform: str | None = Query(None),
    service: AnalyticsService = Depends(get_analytics_service),
) -> list[TopContentResponse]:
    """Get top performing content."""
    try:
        top_list = await service.get_top_content(limit=limit, platform=platform)
        return [TopContentResponse(**item) for item in top_list]
    except Exception as e:
        log.error("Failed to get top content: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


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
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fetch/{content_id}/{platform}")
async def fetch_and_record_stats(
    content_id: UUID,
    platform: str,
    account_id: UUID,
    video_id: str,
    service: AnalyticsService = Depends(get_analytics_service),
    account_repo: SocialAccountRepository = Depends(get_social_account_repository),
) -> dict:
    """Fetch stats from platform API and record them."""
    try:
        account = await account_repo.get_by_id(account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Social account not found")

        from app.models.social_account import SocialPlatform

        platform_enum = SocialPlatform(platform)
        provider = get_provider(platform_enum)
        stats = await provider.fetch_video_stats(
            access_token=account.access_token,
            video_id=video_id,
        )

        metrics = await service.record_metrics(
            content_id=content_id,
            platform=platform,
            views=stats.get("views", 0),
            clicks=stats.get("clicks", 0),
            marketplace_clicks=0,
        )

        return {"success": True, "metrics": metrics}
    except HTTPException:
        raise
    except Exception as e:
        log.error("Failed to fetch and record stats: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


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
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        log.error("Failed to get content recommendations: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


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
        raise HTTPException(status_code=500, detail=str(e))
