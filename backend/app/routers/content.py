"""Content generation router."""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request

from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.dependencies import get_text_generation_service
from app.schemas.generated_content import (
    GenerateContentRequest,
    GenerateContentResponse,
)
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
