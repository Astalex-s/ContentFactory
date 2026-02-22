"""Image generation service: GPT (scene prompt) + Replicate (image-to-image)."""

from __future__ import annotations

import asyncio
import logging
from uuid import UUID

from app.repositories.generated_content import GeneratedContentRepository
from app.repositories.product import ProductRepository
from app.services.ai.ai_factory import get_ai_provider
from app.services.ai.prompt_builder import build_image_scene_prompt
from app.services.image.image_to_image_provider import generate_image_from_image
from app.services.media import MediaStorageService
from app.models.generated_content import ContentStatus, ContentType

log = logging.getLogger(__name__)


class ImageGenerationService:
    """Service for generating product images in different scenes."""

    def __init__(
        self,
        product_repo: ProductRepository,
        content_repo: GeneratedContentRepository,
        media_storage: MediaStorageService,
    ):
        self.product_repo = product_repo
        self.content_repo = content_repo
        self.media_storage = media_storage

    async def generate_images_for_product(
        self,
        product_id: UUID,
        count: int = 3,
    ) -> list[dict]:
        """
        Generate `count` images of the product in different scenes.
        Uses main product image as source. Returns list of created content items.
        """
        product = await self.product_repo.get_by_id(product_id)
        if not product:
            return []

        image_data = await self.product_repo.get_image_data(product_id)
        if not image_data:
            log.warning("Product %s has no image_data", product_id)
            return []

        ai = get_ai_provider()
        created = []

        for i in range(count):
            try:
                scene_prompt_user = build_image_scene_prompt(
                    {
                        "name": product.name,
                        "description": product.description or "",
                        "category": product.category or "",
                    },
                    i,
                )
                scene_text = await ai.generate_text(
                    scene_prompt_user,
                    system_prompt="You generate scene descriptions for image-to-image AI. "
                    "Output ONLY the scene description in English, 2-4 sentences. No other text.",
                )
                scene_text = (scene_text or "").strip()
                if not scene_text:
                    scene_text = "product on white background, soft studio lighting"

                if i > 0:
                    from app.core.config import get_settings

                    delay = get_settings().REPLICATE_DELAY_SECONDS
                    await asyncio.sleep(delay)

                out_bytes = await generate_image_from_image(image_data, scene_text)
                rel_path = self.media_storage.save_image(product_id, out_bytes)

                content = await self.content_repo.create_media(
                    product_id=product_id,
                    content_type=ContentType.IMAGE,
                    file_path=rel_path,
                    content_variant=i + 1,
                    content_text=scene_text,
                    status=ContentStatus.READY,
                )
                created.append(
                    {
                        "id": str(content.id),
                        "file_path": rel_path,
                        "variant": i + 1,
                    }
                )
                log.info("Generated image %d/%d for product %s", i + 1, count, product_id)
            except Exception as e:
                log.exception("Failed to generate image %d for product %s: %s", i + 1, product_id, e)
                raise

        return created
