"""Replicate image-to-image provider (change background/environment)."""

from __future__ import annotations

import asyncio
import logging
import os
import tempfile
import time

import httpx
from replicate import Client

from app.core.config import get_settings

log = logging.getLogger(__name__)

REPLICATE_TIMEOUT = httpx.Timeout(
    connect=60.0, read=300.0, write=60.0, pool=60.0
)
REPLICATE_MAX_RETRIES = 4
REPLICATE_RETRY_DELAY = 10


async def generate_image_from_image(
    image_bytes: bytes,
    scene_prompt: str,
) -> bytes:
    """
    Generate image via Replicate image-to-image (change background/environment).
    Preserves the main object, changes only scene/lighting.
    Returns PNG bytes.
    """
    settings = get_settings()
    token = settings.REPLICATE_API_TOKEN
    if not token:
        raise ValueError("REPLICATE_API_TOKEN is not set")
    os.environ["REPLICATE_API_TOKEN"] = token

    model = settings.REPLICATE_IMAGE_MODEL or "stability-ai/stable-diffusion-img2img:15a3689ee13b0d2616e98820eca31d4c3abcd36672df6afce5cb6feb1d66087d"
    client = Client(api_token=token, timeout=REPLICATE_TIMEOUT)

    def _run() -> bytes:
        last_error = None
        for attempt in range(1, REPLICATE_MAX_RETRIES + 1):
            try:
                with tempfile.NamedTemporaryFile(
                    suffix=".png", delete=False
                ) as tmp:
                    tmp.write(image_bytes)
                    tmp_path = tmp.name
                try:
                    with open(tmp_path, "rb") as img:
                        input_params = {
                            "image": img,
                            "prompt": scene_prompt,
                            "prompt_strength": 0.6,  # preserve product, change scene
                        }
                        output = client.run(model, input=input_params)
                    for out in output:
                        return out.read()
                    raise ValueError("No image returned from Replicate")
                finally:
                    try:
                        os.unlink(tmp_path)
                    except OSError:
                        pass
            except Exception as e:
                if "prompt" in str(e).lower() or "input" in str(e).lower():
                    try:
                        with tempfile.NamedTemporaryFile(
                            suffix=".png", delete=False
                        ) as tmp:
                            tmp.write(image_bytes)
                            tmp_path = tmp.name
                        try:
                            with open(tmp_path, "rb") as img:
                                output = client.run(
                                    model,
                                    input={"image": img},
                                )
                            for out in output:
                                return out.read()
                            raise ValueError("No image returned") from e
                        finally:
                            try:
                                os.unlink(tmp_path)
                            except OSError:
                                pass
                    except Exception as e2:
                        last_error = e2
                else:
                    last_error = e

                if isinstance(last_error, (httpx.TimeoutException, OSError)):
                    log.warning(
                        "Replicate image-to-image failed (attempt %d/%d): %s",
                        attempt,
                        REPLICATE_MAX_RETRIES,
                        last_error,
                    )
                if attempt < REPLICATE_MAX_RETRIES:
                    time.sleep(REPLICATE_RETRY_DELAY)
                else:
                    raise last_error from e
        raise last_error or RuntimeError("Replicate failed")

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _run)
