"""Abstract base class for AI providers."""

from abc import ABC, abstractmethod
from typing import Optional


class AIProvider(ABC):
    """Abstract AI provider interface."""

    @abstractmethod
    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        extra_context: Optional[dict] = None,
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
