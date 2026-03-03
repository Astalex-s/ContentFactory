"""Text generation service."""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from app.core.config import get_settings
from app.models.generated_content import ContentStatus, ContentTextType, Platform, Tone
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
        content_text_type: ContentTextType = ContentTextType.SHORT_POST,
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

        return await self._generate_impl(
            product_id, product_dict, platform, tone, content_text_type
        )

    async def generate_video_title(self, product_id: UUID) -> str | None:
        """
        Generate short Russian video title for product. Returns None if product not found.
        """
        product = await self.product_repo.get_by_id(product_id)
        if product is None:
            return None

        system_prompt = (
            "Ты помощник по созданию заголовков для коротких видео о товарах. "
            "Отвечай только заголовком, без кавычек и пояснений. "
            "Заголовок: короткий (до 60 символов), на русском, релевантный товару."
        )
        user_prompt = (
            f"Товар: {product.name}. "
            f"{f'Описание: {product.description[:200]}' if product.description else ''} "
            "Придумай цепляющий заголовок для YouTube Shorts."
        )

        provider = get_ai_provider()
        try:
            text = await provider.generate_text(
                user_prompt,
                system_prompt,
                extra_context={"product_id": product_id},
            )
            title = (text or "").strip()[:100]
            return title if title else product.name
        except Exception as e:
            ai_log.warning("Video title generation failed: %s", e)
            return product.name

    async def _generate_impl(
        self,
        product_id: UUID,
        product_dict: dict[str, Any],
        platform: Platform,
        tone: Tone,
        content_text_type: ContentTextType,
    ) -> GenerateContentResponse | None:
        """Internal: generate text variants."""
        system_prompt, user_prompt = build_product_prompt(
            product_dict,
            platform.value,
            tone.value,
            content_text_type.value,
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

                max_len = 2000 if content_text_type == ContentTextType.ALL else 800
                text = text.strip()[:max_len]
                content = await self.content_repo.create(
                    product_id=product_id,
                    content_text=text,
                    content_variant=variant_num,
                    platform=platform,
                    tone=tone,
                    content_text_type=content_text_type,
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

    async def generate_post_text(
        self,
        product_id: UUID,
        video_url: str | None = None,
    ) -> tuple[str, str] | None:
        """
        Generate title and text for VK post (optionally with link to video).
        Returns (title, text) or None if product not found.
        """
        product = await self.product_repo.get_by_id(product_id)
        if product is None:
            return None

        link_block = ""
        if video_url and video_url.strip():
            link_block = f"\n\nСмотрите видео: {video_url.strip()}"

        system_prompt = (
            "Ты помощник по созданию постов для VK. "
            "Отвечай в формате JSON: {\"title\": \"...\", \"text\": \"...\"}. "
            "Заголовок: короткий (до 80 символов), цепляющий. "
            "Текст: 2-4 предложения о товаре, призыв посмотреть видео."
        )
        user_prompt = (
            f"Товар: {product.name}. "
            f"{f'Описание: {product.description[:300]}' if product.description else ''} "
            "Создай заголовок и текст поста для VK."
        )

        provider = get_ai_provider()
        try:
            raw = await provider.generate_text(
                user_prompt,
                system_prompt,
                extra_context={"product_id": product_id},
            )
            import json

            text = (raw or "").strip()
            # Try to parse JSON
            for block in (text, text.split("```")[0], text.split("```json")[-1].split("```")[0]):
                try:
                    block = block.strip()
                    if block.startswith("{"):
                        obj = json.loads(block)
                        title = (obj.get("title") or product.name)[:200]
                        body = (obj.get("text") or "")[:2000]
                        return (title, (body + link_block).strip())
                except (json.JSONDecodeError, TypeError):
                    continue
            # Fallback: first line = title, rest = text
            lines = text.split("\n")
            title = (lines[0] or product.name)[:200].strip()
            body = "\n".join(lines[1:]).strip()[:2000] if len(lines) > 1 else ""
            return (title, (body + link_block).strip() or product.name)
        except Exception as e:
            ai_log.warning("Post text generation failed: %s", e)
            title = product.name[:200]
            text = (f"Узнайте больше о {product.name}!" + link_block).strip()
            return (title, text)
