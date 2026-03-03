"""Video generation service: GPT (script) + Replicate (image-to-video)."""

from __future__ import annotations

import asyncio
import json
import logging
from uuid import UUID

from app.core.config import get_settings
from app.interfaces.storage import StorageInterface
from app.models.generated_content import ContentStatus, ContentType
from app.repositories.generated_content import GeneratedContentRepository
from app.repositories.product import ProductRepository
from app.services.ai.ai_factory import get_ai_provider
from app.services.media import build_video_key
from app.services.tts import generate_speech
from app.services.video import generate_video_from_image
from app.services.video.video_overlay import (
    add_voiceover,
    append_qr_endcard,
    concat_videos,
    extract_last_frame,
)

log = logging.getLogger(__name__)

VIDEO_SCRIPT_PROMPT = """Product: {name}
Category: {category}
Description: {description}

Generate a video prompt in English for image-to-video AI (Wan/Kling).
CRITICAL: The product in the image must stay EXACTLY the same — no shape change, no morphing, no objects passing through each other.
Describe ONE simple, slow action: person gently picks up or touches the product. Avoid close-ups of hands. No complex hand gestures.
Use words: subtle, gentle, slight, minimal motion, smooth. Natural lighting, stable camera.
Output: 1-2 sentences, max 60 words. English only.
AVOID: extra fingers, overlapping objects, object transformation, sudden changes, warping.
"""

VIDEO_SEGMENTS_PROMPT = """Product: {name}
Category: {category}
Description: {description}

Generate exactly 5 sequential video prompts in English for image-to-video AI (Wan/Kling).
Each prompt describes ONE 5-second clip. Clips form a continuous story: person discovers product → picks up → uses → shows result → satisfied reaction.

CRITICAL:
- Product must stay EXACTLY the same in all clips — no morphing, no objects passing through each other.
- Use: subtle, gentle, slight, minimal motion, smooth. Avoid close-ups of hands. No complex hand gestures.
- Output format: JSON object with key "prompts" containing array of 5 strings. Example: {{"prompts": ["Clip 1...", "Clip 2...", ...]}}
- Each prompt: 1–2 sentences, max 50 words. English only.
- AVOID: extra fingers, overlapping objects, object transformation, sudden changes, warping.

Output ONLY valid JSON, no markdown."""

VIDEO_VOICEOVER_PROMPT = """Product: {name}
Category: {category}
Description: {description}

Generate a short advertising voiceover script in Russian for a product video. Duration: ~20–25 seconds when spoken.
Structure: hook (1–2 sec) → key benefit (5–7 sec) → call to action (2–3 sec).
Tone: friendly, energetic, persuasive. No more than 50 words.
Output: ONLY the script text, nothing else."""


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

        settings = get_settings()
        segments_count = max(1, settings.REPLICATE_VIDEO_SEGMENTS or 1)
        segment_duration = max(5, min(7, settings.REPLICATE_VIDEO_SEGMENT_DURATION or 5))

        if segments_count > 1:
            out_bytes, script = await self._generate_segmented_video(
                image_bytes=image_bytes,
                product=product,
                segments_count=segments_count,
                segment_duration=segment_duration,
            )
        else:
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
            out_bytes = await generate_video_from_image(
                image_bytes, script, segment_duration=segment_duration
            )

        if settings.TTS_PROVIDER and settings.TTS_PROVIDER.strip():
            voiceover_text = await self._generate_voiceover_text(product)
            if voiceover_text:
                audio_bytes = await generate_speech(voiceover_text)
                if audio_bytes:
                    out_bytes = await asyncio.to_thread(add_voiceover, out_bytes, audio_bytes)

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

    async def _generate_voiceover_text(self, product) -> str:
        """Generate voiceover script via GPT."""
        ai = get_ai_provider()
        raw = await ai.generate_text(
            VIDEO_VOICEOVER_PROMPT.format(
                name=product.name,
                category=product.category or "",
                description=(product.description or "")[:500],
            ),
            system_prompt="You generate voiceover scripts. Output ONLY the script text.",
        )
        return (raw or "").strip() or ""

    async def _generate_segmented_video(
        self,
        image_bytes: bytes,
        product,
        segments_count: int,
        segment_duration: int,
    ) -> tuple[bytes, str]:
        """Generate video from 5 segments, concat, return (video_bytes, script_summary)."""
        ai = get_ai_provider()
        segments_prompt = VIDEO_SEGMENTS_PROMPT.format(
            name=product.name,
            category=product.category or "",
            description=(product.description or "")[:500],
        )
        raw = await ai.generate_text(
            segments_prompt,
            system_prompt="You generate video scripts. Output ONLY valid JSON.",
        )
        prompts = self._parse_segments_json(raw, segments_count)
        settings = get_settings()
        delay = settings.REPLICATE_DELAY_SECONDS or 15

        clips: list[bytes] = []
        current_image = image_bytes
        last_frame: bytes | None = None

        for i, prompt in enumerate(prompts):
            if i > 0:
                await asyncio.sleep(delay)
            clip_bytes = await generate_video_from_image(
                current_image,
                prompt=prompt,
                last_image_bytes=None,
                segment_duration=segment_duration,
            )
            clips.append(clip_bytes)
            last_frame = await asyncio.to_thread(extract_last_frame, clip_bytes)
            if not last_frame:
                last_frame = None
                current_image = image_bytes
            else:
                current_image = last_frame

        out_bytes = await asyncio.to_thread(concat_videos, clips)
        script_summary = " | ".join(p[:80] for p in prompts[:3])
        if len(prompts) > 3:
            script_summary += "..."
        return out_bytes, script_summary[:500]

    def _parse_segments_json(self, raw: str, count: int) -> list[str]:
        """Parse GPT JSON response to list of prompts. Fallback on error."""
        fallback = "Smooth motion, realistic movement. Maintain the style of the image."
        raw = (raw or "").strip()
        if raw.startswith("```"):
            lines = raw.split("\n")
            start = 0
            for i, line in enumerate(lines):
                if "```" in line:
                    start = i + 1
                    break
            raw = "\n".join(lines[start:])
        try:
            data = json.loads(raw)
            prompts = data.get("prompts") if isinstance(data, dict) else None
            if isinstance(prompts, list) and len(prompts) >= count:
                return [str(p).strip() or fallback for p in prompts[:count]]
        except json.JSONDecodeError:
            pass
        return [fallback] * count
