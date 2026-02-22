"""Replicate image-to-video provider."""

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
    connect=60.0, read=600.0, write=60.0, pool=60.0
)
REPLICATE_MAX_RETRIES = 3
REPLICATE_RETRY_DELAY = 15


async def generate_video_from_image(
    image_bytes: bytes,
    prompt: str | None = None,
) -> bytes:
    """
    Generate video from image via Replicate image-to-video.
    Returns MP4 bytes.
    """
    settings = get_settings()
    token = settings.REPLICATE_API_TOKEN
    if not token:
        raise ValueError("REPLICATE_API_TOKEN is not set")
    os.environ["REPLICATE_API_TOKEN"] = token

    model = settings.REPLICATE_VIDEO_MODEL or "kwaivgi/kling-v2.1:daad218feb714b03e2a1ac445986aebb9d05243cd00da2af17be2e4049f48f69"
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
                        if "kling" in model.lower():
                            duration = min(20, max(5, settings.REPLICATE_VIDEO_DURATION))
                            input_params = {
                                "start_image": img,
                                "prompt": prompt or "Smooth motion, realistic movement",
                                "duration": duration,
                            }
                        else:
                            input_params = {"input_image": img}
                            if "stable-video-diffusion" in model or "christophy" in model:
                                input_params["video_length"] = "25_frames_with_svd_xt"
                                input_params["frames_per_second"] = 6

                        output = client.run(model, input=input_params)
                    items = list(output)
                    if not items:
                        raise ValueError("No video returned from Replicate")
                    first = items[0]
                    if hasattr(first, "read"):
                        return first.read()
                    # Replicate video models return iterator of byte chunks
                    return b"".join(items)
                finally:
                    try:
                        os.unlink(tmp_path)
                    except OSError:
                        pass
            except Exception as e:
                last_error = e
                if "input_image" in str(e) or "input" in str(e).lower():
                    try:
                        with tempfile.NamedTemporaryFile(
                            suffix=".png", delete=False
                        ) as tmp:
                            tmp.write(image_bytes)
                            tmp_path = tmp.name
                        try:
                            with open(tmp_path, "rb") as img:
                                input_params = {"image": img}
                                output = client.run(model, input=input_params)
                            items = list(output)
                            if not items:
                                raise ValueError("No video returned") from e
                            first = items[0]
                            if hasattr(first, "read"):
                                return first.read()
                            return b"".join(items)
                        finally:
                            try:
                                os.unlink(tmp_path)
                            except OSError:
                                pass
                    except Exception as e2:
                        last_error = e2

                if isinstance(last_error, (httpx.TimeoutException, OSError)):
                    log.warning(
                        "Replicate video failed (attempt %d/%d): %s",
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
