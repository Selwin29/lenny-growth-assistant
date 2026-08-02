from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseLLMProvider(ABC):
    """Abstract base class representing an LLM Provider interface contract."""

    @abstractmethod
    async def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        temperature: float = 0.2, 
        max_tokens: int = 1500,
        **kwargs
    ) -> str:
        """Generate a response text from the LLM given the message context history.

        Args:
            messages: List of message dicts with 'role' and 'content'.
            temperature: LLM sampling temperature.
            max_tokens: Maximum number of tokens to generate.

        Raises:
            LLMError: If any generation or provider error occurs.
        """
        pass
