"""Content generation router."""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.dependencies import get_content_service, get_text_generation_service
from app.schemas.generated_content import (
    ContentListResponse,
    GenerateContentRequest,
    GenerateContentResponse,
    UpdateContentRequest,
)
from app.services.content_service import ContentService
from app.services.text_generation_service import TextGenerationService

log = logging.getLogger(__name__)

router = APIRouter(prefix="/content", tags=["content"])


@router.post(
    "/generate/{product_id}",
    response_model=GenerateContentResponse,
)
@limiter.limit(get_settings().CONTENT_GENERATE_RATE_LIMIT)
async def generate_content(
    request: Request,
    product_id: UUID,
    body: GenerateContentRequest,
    service: TextGenerationService = Depends(get_text_generation_service),
) -> GenerateContentResponse:
    """
    Generate text content variants for product.

    Returns 404 if product not found.
    """
    try:
        result = await service.generate_for_product(
            product_id=product_id,
            platform=body.platform,
            tone=body.tone,
            content_text_type=body.content_text_type,
        )
    except Exception as e:
        log.error("Content generation failed: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail="Ошибка генерации контента. Попробуйте позже.",
        ) from e

    if result is None:
        raise HTTPException(status_code=404, detail="Товар не найден")

    return result


@router.get("/product/{product_id}/has")
async def has_content(
    product_id: UUID,
    service: ContentService = Depends(get_content_service),
) -> dict:
    """Check if product has any generated content."""
    return {"has_content": await service.has_content(product_id)}


@router.get(
    "/product/{product_id}",
    response_model=ContentListResponse,
)
async def list_content_by_product(
    product_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: ContentService = Depends(get_content_service),
) -> ContentListResponse:
    """Get paginated list of generated content for product."""
    return await service.get_by_product(
        product_id=product_id,
        page=page,
        page_size=page_size,
    )


@router.patch("/{content_id}")
async def update_content(
    content_id: UUID,
    body: UpdateContentRequest,
    service: ContentService = Depends(get_content_service),
):
    """Update content text (draft only)."""
    result = await service.update_text(content_id, body.content_text)
    if result is None:
        raise HTTPException(
            status_code=400,
            detail="Контент не найден или редактирование недоступно (только draft).",
        )
    return result


@router.delete("/{content_id}", status_code=204)
async def delete_content(
    content_id: UUID,
    service: ContentService = Depends(get_content_service),
) -> None:
    """Delete content."""
    deleted = await service.delete(content_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Контент не найден")
