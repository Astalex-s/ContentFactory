"""Abstract base class for AI providers."""

from abc import ABC, abstractmethod


class AIProvider(ABC):
    """Abstract AI provider interface."""

    @abstractmethod
    async def generate_text(
        self,
        prompt: str,
        system_prompt: str | None = None,
        extra_context: dict | None = None,
    ) -> str:
        """
        Generate text from prompt.

        Args:
            prompt: Input prompt string.
            system_prompt: Optional system instructions.
            extra_context: Optional context for logging (e.g. product_id).

        Returns:
            Generated text.

        Raises:
            TimeoutError: On request timeout.
            Exception: On provider errors.
        """
        ...
