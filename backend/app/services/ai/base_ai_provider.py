"""Abstract base class for AI providers."""

from abc import ABC, abstractmethod


class AIProvider(ABC):
    """Abstract AI provider interface."""

    @abstractmethod
    async def generate_text(self, prompt: str) -> str:
        """
        Generate text from prompt.

        Args:
            prompt: Input prompt string.

        Returns:
            Generated text.

        Raises:
            TimeoutError: On request timeout.
            Exception: On provider errors.
        """
        ...
