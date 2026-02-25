"""Dashboard router."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from app.core.database import get_db
from app.repositories.dashboard import DashboardRepository
from app.repositories.analytics import AnalyticsRepository
from app.repositories.generated_content import GeneratedContentRepository
from app.repositories.product import ProductRepository
from app.schemas.dashboard import DashboardStatsResponse
from app.services.dashboard_service import DashboardService
from app.services.recommendation_service import RecommendationService
from sqlalchemy.ext.asyncio import AsyncSession


def get_dashboard_service(
    db: AsyncSession = Depends(get_db),
) -> DashboardService:
    """Dependency: DashboardService instance."""
    return DashboardService(DashboardRepository(db))


def get_recommendation_service(
    db: AsyncSession = Depends(get_db),
) -> RecommendationService:
    """Dependency: RecommendationService instance."""
    return RecommendationService(
        AnalyticsRepository(db),
        GeneratedContentRepository(db),
        ProductRepository(db),
    )


router = APIRouter(prefix="/dashboard", tags=["dashboard"])
log = logging.getLogger(__name__)


@router.get("/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    service: DashboardService = Depends(get_dashboard_service),
) -> DashboardStatsResponse:
    """Get dashboard statistics."""
    try:
        stats = await service.get_stats()
        return DashboardStatsResponse(
            pipeline=stats["pipeline"],
            alerts=stats["alerts"],
        )
    except Exception as e:
        log.error("Failed to get dashboard stats: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/recommendations")
async def get_dashboard_recommendations(
    service: RecommendationService = Depends(get_recommendation_service),
) -> dict:
    """Get AI recommendations for dashboard."""
    try:
        recommendations = await service.get_general_recommendations()
        return recommendations
    except Exception as e:
        log.error("Failed to get dashboard recommendations: %s", e)
        raise HTTPException(status_code=500, detail="Failed to get AI recommendations")
