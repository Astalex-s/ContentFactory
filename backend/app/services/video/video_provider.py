"""Replicate image-to-video provider."""

from __future__ import annotations

import asyncio
import logging
import os
import tempfile
import time

import httpx
from replicate.client import Client
from replicate.exceptions import ReplicateError

from app.core.config import get_settings
from app.services.replicate_rate_limiter import (
    mark_replicate_request_complete,
    wait_before_replicate_request,
)

log = logging.getLogger(__name__)

REPLICATE_TIMEOUT = httpx.Timeout(connect=60.0, read=600.0, write=60.0, pool=60.0)
REPLICATE_MAX_RETRIES = 8  # retries for 429, 500, 503, etc.
REPLICATE_RETRY_DELAY = 15
REPLICATE_RATE_LIMIT_DELAY = 20  # wait before retry on API errors


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

    model = (
        settings.REPLICATE_VIDEO_MODEL
        or "wan-video/wan-2.2-i2v-fast:febae7d9656309cf8c5df4842b27ae4768c0e47a0e1ce443a5ae81f896956134"
    )
    if ":" not in model:
        if "kling" in model.lower():
            model = f"{model}:daad218feb714b03e2a1ac445986aebb9d05243cd00da2af17be2e4049f48f69"
        elif "veo" in model.lower():
            model = f"{model}:79ad4a4291af114fc8905c6e509d5e6fb5c09a255c29dd92b5a9db0c806ed61d"
        elif "wan" in model.lower() or "i2v" in model.lower():
            model = f"{model}:febae7d9656309cf8c5df4842b27ae4768c0e47a0e1ce443a5ae81f896956134"
    client = Client(api_token=token, timeout=REPLICATE_TIMEOUT)

    def _run() -> bytes:
        last_error = None
        for attempt in range(1, REPLICATE_MAX_RETRIES + 1):
            try:
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                    tmp.write(image_bytes)
                    tmp_path = tmp.name
                try:
                    with open(tmp_path, "rb") as img:
                        input_params: dict[str, object]
                        if "wan" in model.lower() or "i2v" in model.lower():
                            d = settings.REPLICATE_VIDEO_DURATION
                            num_frames = 81 if d <= 5 else (101 if d <= 7 else 121)
                            input_params = {
                                "image": img,
                                "prompt": prompt
                                or "Smooth motion, realistic movement. Maintain the style of the image.",
                                "num_frames": num_frames,
                                "go_fast": True,
                            }
                        elif "veo" in model.lower():
                            d = min(8, max(4, settings.REPLICATE_VIDEO_DURATION))
                            duration = 4 if d <= 5 else (6 if d <= 7 else 8)
                            input_params = {
                                "image": img,
                                "prompt": prompt
                                or "Smooth motion, realistic movement. Maintain the style of the image.",
                                "duration": duration,
                                "aspect_ratio": "16:9",
                            }
                        elif "kling" in model.lower():
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

                        wait_before_replicate_request()
                        try:
                            output = client.run(model, input=input_params)
                        finally:
                            mark_replicate_request_complete()
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
                if isinstance(e, ReplicateError):
                    status = getattr(e, "status", None)
                    log.warning(
                        "Replicate API error (status=%s), retry in %ds (attempt %d/%d): %s",
                        status,
                        REPLICATE_RATE_LIMIT_DELAY,
                        attempt,
                        REPLICATE_MAX_RETRIES,
                        getattr(e, "detail", str(e))[:200],
                    )
                    if attempt < REPLICATE_MAX_RETRIES:
                        time.sleep(REPLICATE_RATE_LIMIT_DELAY)
                        continue
                    raise last_error from e
                # Fallback only for SVD etc (Kling/Veo/Wan have specific params)
                if (
                    ("input_image" in str(e) or "input" in str(e).lower())
                    and "kling" not in model.lower()
                    and "veo" not in model.lower()
                    and "wan" not in model.lower()
                ):
                    try:
                        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                            tmp.write(image_bytes)
                            tmp_path = tmp.name
                        try:
                            with open(tmp_path, "rb") as img:
                                input_params = {"image": img}
                                wait_before_replicate_request()
                                try:
                                    output = client.run(model, input=input_params)
                                finally:
                                    mark_replicate_request_complete()
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

                if isinstance(last_error, ReplicateError):
                    log.warning(
                        "Replicate API error on fallback (status=%s), retry in %ds (attempt %d/%d)",
                        getattr(last_error, "status", None),
                        REPLICATE_RATE_LIMIT_DELAY,
                        attempt,
                        REPLICATE_MAX_RETRIES,
                    )
                    if attempt < REPLICATE_MAX_RETRIES:
                        time.sleep(REPLICATE_RATE_LIMIT_DELAY)
                        continue
                    raise last_error from e
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
