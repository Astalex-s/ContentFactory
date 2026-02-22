"""Replicate image generation provider (SDXL)."""

from __future__ import annotations

import asyncio
import logging
import replicate

from app.core.config import get_settings

log = logging.getLogger(__name__)

REPLICATE_SDXL_MODEL = "stability-ai/sdxl"


async def generate_image_replicate(prompt: str) -> bytes:
    """
    Generate image via Replicate SDXL.
    Returns PNG bytes.
    """
    settings = get_settings()
    token = settings.REPLICATE_API_TOKEN
    if not token:
        raise ValueError("REPLICATE_API_TOKEN is not set")

    def _run() -> bytes:
        output = replicate.run(
            REPLICATE_SDXL_MODEL,
            input={
                "prompt": prompt,
                "num_outputs": 1,
                "guidance_scale": 7.5,
            },
        )
        for image in output:
            return image.read()
        raise ValueError("No image returned from Replicate")

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _run)
