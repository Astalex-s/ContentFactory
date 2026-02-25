"""Dashboard schemas."""

from __future__ import annotations

from pydantic import BaseModel


class DashboardPipeline(BaseModel):
    """Pipeline statistics."""

    imported: int
    text_generated: int
    media_generated: int
    scheduled: int
    published: int
    with_analytics: int


class DashboardAlerts(BaseModel):
    """Dashboard alerts."""

    products_no_content: int
    publication_failed: int
    low_ctr_count: int
    ai_errors_count: int


class DashboardStatsResponse(BaseModel):
    """Dashboard statistics response."""

    pipeline: DashboardPipeline
    alerts: DashboardAlerts
