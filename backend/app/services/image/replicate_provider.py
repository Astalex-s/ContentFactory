"""Replicate image generation provider (SDXL)."""

from __future__ import annotations

import asyncio
import logging
import os
import time

import httpx
from replicate import Client

from app.core.config import get_settings

log = logging.getLogger(__name__)

REPLICATE_SDXL_MODEL = "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b"

# Таймауты: connect 60s (SSL handshake), read 300s (генерация SDXL)
REPLICATE_TIMEOUT = httpx.Timeout(
    connect=60.0, read=300.0, write=60.0, pool=60.0
)
REPLICATE_MAX_RETRIES = 4
REPLICATE_RETRY_DELAY = 10


async def generate_image_replicate(prompt: str) -> bytes:
    """
    Generate image via Replicate SDXL.
    Retries on ConnectTimeout/ReadTimeout. Returns PNG bytes.
    """
    settings = get_settings()
    token = settings.REPLICATE_API_TOKEN
    if not token:
        raise ValueError("REPLICATE_API_TOKEN is not set")
    os.environ["REPLICATE_API_TOKEN"] = token

    client = Client(api_token=token, timeout=REPLICATE_TIMEOUT)

    def _run() -> bytes:
        last_error = None
        for attempt in range(1, REPLICATE_MAX_RETRIES + 1):
            try:
                output = client.run(
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
            except (httpx.TimeoutException, OSError) as e:
                last_error = e
                log.warning(
                    "Replicate request failed (attempt %d/%d): %s",
                    attempt,
                    REPLICATE_MAX_RETRIES,
                    e,
                )
                if attempt < REPLICATE_MAX_RETRIES:
                    time.sleep(REPLICATE_RETRY_DELAY)
                else:
                    raise last_error from e
        raise last_error or RuntimeError("Replicate failed")

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _run)
