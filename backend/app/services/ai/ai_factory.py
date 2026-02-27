"""Factory for AI provider selection."""

import logging

from app.core.config import get_settings
from app.services.ai.base_ai_provider import AIProvider
from app.services.ai.openai_provider import OpenAIProvider

log = logging.getLogger(__name__)

_PROVIDER_REGISTRY: dict[str, type[AIProvider]] = {
    "openai": OpenAIProvider,
}


def get_ai_provider(
    provider_name: str | None = None,
    **kwargs,
) -> AIProvider:
    """
    Create AI provider instance.

    Args:
        provider_name: Provider key (e.g. 'openai'). From AI_PROVIDER env if omitted.
        **kwargs: Passed to provider constructor.

    Returns:
        Configured AIProvider instance.

    Raises:
        ValueError: If provider is unknown.
    """
    settings = get_settings()
    name = provider_name or settings.AI_PROVIDER or "openai"

    if name not in _PROVIDER_REGISTRY:
        raise ValueError(
            f"Unknown AI provider: {name}. Available: {list(_PROVIDER_REGISTRY.keys())}"
        )

    cls = _PROVIDER_REGISTRY[name]
    return cls(**kwargs)


def register_provider(name: str, provider_class: type[AIProvider]) -> None:
    """Register a new AI provider for easy extension."""
    _PROVIDER_REGISTRY[name] = provider_class
    log.info("Registered AI provider: %s", name)
