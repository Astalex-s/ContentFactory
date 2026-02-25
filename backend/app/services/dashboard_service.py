"""Dashboard service."""

from __future__ import annotations

from app.repositories.dashboard import DashboardRepository


class DashboardService:
    """Service for dashboard statistics."""

    def __init__(self, dashboard_repo: DashboardRepository):
        self.dashboard_repo = dashboard_repo

    async def get_stats(self) -> dict:
        """Get aggregated dashboard statistics."""
        total_products = await self.dashboard_repo.get_total_products()
        
        # Content Pipeline
        text_generated = await self.dashboard_repo.get_text_generated_count()
        media_generated = await self.dashboard_repo.get_media_generated_count()
        scheduled = await self.dashboard_repo.get_scheduled_count()
        published = await self.dashboard_repo.get_published_count()
        with_analytics = await self.dashboard_repo.get_analytics_count()

        # Alerts
        failed_publications = await self.dashboard_repo.get_failed_publication_count()
        low_ctr = await self.dashboard_repo.get_low_ctr_count()
        
        # Products without content
        products_with_any_content = await self.dashboard_repo.get_products_with_content_count()
        products_no_content = max(0, total_products - products_with_any_content)

        return {
            "pipeline": {
                "imported": total_products,
                "text_generated": text_generated,
                "media_generated": media_generated,
                "scheduled": scheduled,
                "published": published,
                "with_analytics": with_analytics,
            },
            "alerts": {
                "products_no_content": products_no_content,
                "publication_failed": failed_publications,
                "low_ctr_count": low_ctr,
                "ai_errors_count": 0,  # Placeholder, requires error logging table
            },
        }
