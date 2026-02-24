"""
Global rate limiter for Replicate API.
Ensures minimum interval between requests to avoid 429.
Thread-safe; used by image and video providers.
"""

from __future__ import annotations

import logging
import threading
import time

from app.core.config import get_settings

log = logging.getLogger(__name__)

_lock = threading.Lock()
_last_request_end_time: float = 0
_FIRST_REQUEST_DELAY = 5  # seconds before first request (cool-down from prior bursts)


def wait_before_replicate_request() -> None:
    """
    Block until we can make a Replicate request (min interval since last completed).
    Call before client.run(). Thread-safe.
    """
    global _last_request_end_time
    settings = get_settings()
    min_interval = max(10, settings.REPLICATE_DELAY_SECONDS)  # 6 req/min needs ~10s

    with _lock:
        now = time.time()
        if _last_request_end_time == 0:
            # First request: short delay to avoid burst from prior session
            log.info("Replicate rate limiter: first request, waiting %ds", _FIRST_REQUEST_DELAY)
            time.sleep(_FIRST_REQUEST_DELAY)
        else:
            wait_until = _last_request_end_time + min_interval
            if now < wait_until:
                sleep_time = wait_until - now
                log.info("Replicate rate limiter: waiting %.0fs before request", sleep_time)
                time.sleep(sleep_time)


def mark_replicate_request_complete() -> None:
    """Call after Replicate request completes (success or failure). Thread-safe."""
    global _last_request_end_time
    with _lock:
        _last_request_end_time = time.time()
