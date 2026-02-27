"""Video generation service: GPT (script) + Replicate (image-to-video)."""

from __future__ import annotations

import asyncio
import logging
from uuid import UUID

from app.repositories.generated_content import GeneratedContentRepository
from app.repositories.product import ProductRepository
from app.services.ai.ai_factory import get_ai_provider
from app.services.media import build_video_key
from app.services.video import generate_video_from_image
from app.interfaces.storage import StorageInterface
from app.services.video.video_overlay import append_qr_endcard
from app.models.generated_content import ContentStatus, ContentType

log = logging.getLogger(__name__)

VIDEO_SCRIPT_PROMPT = """Product: {name}
Category: {category}
Description: {description}

Generate a concise video prompt in English for image-to-video AI (Kling). 
The video must show a REAL PERSON using the product realistically and attractively for advertising (YouTube/VK Shorts).
Describe typical usage based on the description: person picks up the product, uses it exactly as intended (e.g., potholders — removes hot baking sheet from oven to counter; dish rack — washes dishes and places them to dry).
Natural, smooth movements, bright lighting, appetizing kitchen/scene. Only facts from the description — no inventions.
Output: 1-2 sentences, max 80 words. English only.
Example: "A young woman grabs the silicone potholders, lifts a steaming hot baking tray from the oven, and places it safely on the kitchen counter."
"""


class VideoGenerationService:
    """Service for generating product usage videos."""

    def __init__(
        self,
        product_repo: ProductRepository,
        content_repo: GeneratedContentRepository,
        media_storage: StorageInterface,
    ):
        self.product_repo = product_repo
        self.content_repo = content_repo
        self.media_storage = media_storage

    async def generate_video_for_product(
        self,
        product_id: UUID,
        image_content_id: UUID | None = None,
    ) -> dict | None:
        """
        Generate video from product image or from a generated image.
        If image_content_id is None, uses main product image.
        Returns created content item or None.
        """
        product = await self.product_repo.get_by_id(product_id)
        if not product:
            return None

        image_bytes = None
        if image_content_id:
            content_item = await self.content_repo.get_by_id(image_content_id)
            if (
                content_item
                and content_item.content_type == ContentType.IMAGE
                and content_item.file_path
            ):
                image_bytes = await self.media_storage.download(content_item.file_path)

        if not image_bytes:
            image_bytes = await self.product_repo.get_image_data(product_id)

        if not image_bytes:
            log.warning("Product %s has no image", product_id)
            return None

        ai = get_ai_provider()
        script_prompt = VIDEO_SCRIPT_PROMPT.format(
            name=product.name,
            category=product.category or "",
            description=(product.description or "")[:500],
        )
        script = await ai.generate_text(
            script_prompt,
            system_prompt="You generate video scripts for AI. Output ONLY the script in English.",
        )
        script = (script or "").strip() or "Person using product in realistic setting"

        out_bytes = await generate_video_from_image(image_bytes, script)
        if product.marketplace_url:
            out_bytes = await asyncio.to_thread(
                append_qr_endcard, out_bytes, product.marketplace_url
            )
        key = build_video_key(str(product_id), "mp4")
        rel_path = await self.media_storage.upload(key, out_bytes, "video/mp4")

        content = await self.content_repo.create_media(
            product_id=product_id,
            content_type=ContentType.VIDEO,
            file_path=rel_path,
            content_variant=1,
            content_text=script,
            status=ContentStatus.READY,
        )
        log.info("Generated video for product %s", product_id)
        return {
            "id": str(content.id),
            "file_path": rel_path,
        }
