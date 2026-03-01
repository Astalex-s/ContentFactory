"""Cache for publish rate limit setting. Updated at startup and when settings change."""

_publish_rate_limit_enabled: bool = True


def is_publish_rate_limit_enabled() -> bool:
    """Return True if rate limit should be applied to publish endpoints."""
    return _publish_rate_limit_enabled


def set_publish_rate_limit_enabled(enabled: bool) -> None:
    """Update cached value (called from settings or startup)."""
    global _publish_rate_limit_enabled
    _publish_rate_limit_enabled = enabled
