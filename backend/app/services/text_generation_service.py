"""Text generation service."""

from __future__ import annotations

import logging
from uuid import UUID

from app.core.config import get_settings
from app.models.generated_content import ContentStatus, Platform, Tone
from app.repositories.generated_content import GeneratedContentRepository
from app.repositories.product import ProductRepository
from app.schemas.generated_content import (
    GenerateContentResponse,
    GeneratedVariantResponse,
)
from app.services.ai import build_product_prompt, get_ai_provider

log = logging.getLogger(__name__)
ai_log = logging.getLogger("app.ai")


class TextGenerationService:
    """Service for AI text generation."""

    def __init__(
        self,
        product_repository: ProductRepository,
        content_repository: GeneratedContentRepository,
    ):
        self.product_repo = product_repository
        self.content_repo = content_repository

    async def generate_for_product(
        self,
        product_id: UUID,
        platform: Platform,
        tone: Tone,
    ) -> GenerateContentResponse | None:
        """
        Generate 3 text variants for product and save to DB.

        Returns:
            GenerateContentResponse with variants, or None if product not found.
        """
        product = await self.product_repo.get_by_id(product_id)
        if product is None:
            return None

        product_dict = {
            "name": product.name,
            "description": product.description,
            "category": product.category,
            "price": product.price,
        }

        system_prompt, user_prompt = build_product_prompt(
            product_dict, platform.value, tone.value
        )
        provider = get_ai_provider()
        model_name = get_settings().OPENAI_MODEL

        variants: list[GeneratedVariantResponse] = []
        status = ContentStatus.DRAFT

        for variant_num in range(1, 4):
            try:
                text = await provider.generate_text(
                    user_prompt,
                    system_prompt,
                    extra_context={"product_id": product_id},
                )
                if not text or len(text.strip()) == 0:
                    ai_log.warning(
                        "Empty AI response for product_id=%s variant=%d",
                        product_id,
                        variant_num,
                    )
                    continue

                text = text.strip()[:800]
                content = await self.content_repo.create(
                    product_id=product_id,
                    content_text=text,
                    content_variant=variant_num,
                    platform=platform,
                    tone=tone,
                    ai_model=model_name,
                    status=status,
                )
                variants.append(
                    GeneratedVariantResponse(
                        id=content.id,
                        text=content.content_text or "",
                        variant=content.content_variant,
                    )
                )
            except Exception as e:
                ai_log.error(
                    "AI generation failed for product_id=%s variant=%d: %s",
                    product_id,
                    variant_num,
                    str(e),
                    exc_info=True,
                )
                raise

        return GenerateContentResponse(
            product_id=product_id,
            generated_variants=variants,
        )
