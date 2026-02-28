"""Image generation service: GPT (scene prompt) + Replicate (image-to-image)."""

from __future__ import annotations

import logging
from uuid import UUID

from app.interfaces.storage import StorageInterface
from app.models.generated_content import ContentStatus, ContentType
from app.repositories.generated_content import GeneratedContentRepository
from app.repositories.product import ProductRepository
from app.services.ai.ai_factory import get_ai_provider
from app.services.ai.prompt_builder import build_single_image_prompt
from app.services.image.image_to_image_provider import generate_image_from_image
from app.services.media import build_image_key

log = logging.getLogger(__name__)


class ImageGenerationService:
    """Service for generating product image in a single scene."""

    def __init__(
        self,
        product_repo: ProductRepository,
        content_repo: GeneratedContentRepository,
        media_storage: StorageInterface,
    ):
        self.product_repo = product_repo
        self.content_repo = content_repo
        self.media_storage = media_storage

    async def generate_images_for_product(
        self,
        product_id: UUID,
        count: int = 1,
    ) -> list[dict]:
        """
        Generate one image of the product in a scene.
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

        user_prompt = build_single_image_prompt(
            {
                "name": product.name,
                "description": product.description or "",
                "category": product.category or "",
            }
        )
        system_prompt = (
            "You generate a single scene description for image-to-image AI. "
            "Output ONLY the scene description in English. No other text, no introduction."
        )
        raw_response = await ai.generate_text(user_prompt, system_prompt=system_prompt)
        scene_text = (
            raw_response or ""
        ).strip() or "product on white background, soft studio lighting"

        try:
            out_bytes = await generate_image_from_image(image_data, scene_text)
            key = build_image_key(str(product_id), "png")
            rel_path = await self.media_storage.upload(key, out_bytes, "image/png")

            content = await self.content_repo.create_media(
                product_id=product_id,
                content_type=ContentType.IMAGE,
                file_path=rel_path,
                content_variant=1,
                content_text=scene_text,
                status=ContentStatus.READY,
            )
            created.append(
                {
                    "id": str(content.id),
                    "file_path": rel_path,
                    "variant": 1,
                }
            )
            log.info("Generated image for product %s", product_id)
        except Exception as e:
            log.exception("Failed to generate image for product %s: %s", product_id, e)
            raise

        return created
