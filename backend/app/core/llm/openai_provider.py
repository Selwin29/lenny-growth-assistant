import logging
from typing import List, Dict, Any
from openai import AsyncOpenAI, OpenAIError, APIStatusError, APITimeoutError, APIConnectionError

from app.core.config import settings
from app.core.llm.base import BaseLLMProvider
from app.core.llm.exceptions import (
    LLMConfigurationError,
    LLMProviderConnectionError,
    LLMTimeoutError,
    LLMError,
)

logger = logging.getLogger(__name__)

class OpenAIProvider(BaseLLMProvider):
    """OpenAI API implementation of the BaseLLMProvider contract."""

    def __init__(self, api_key: str = "", model: str = "gpt-4o-mini"):
        self.api_key = api_key or settings.OPENAI_API_KEY
        if not self.api_key or "your-openai-api-key" in self.api_key:
            raise LLMConfigurationError("OpenAI API key is missing or set to placeholder value.")
        
        self.model = model
        self.client = AsyncOpenAI(api_key=self.api_key)

    async def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        temperature: float = 0.2, 
        max_tokens: int = 1500,
        **kwargs
    ) -> str:
        try:
            logger.info("Sending chat completion request to OpenAI (model=%s)", self.model)
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            return response.choices[0].message.content or ""
        except APITimeoutError as e:
            logger.error("OpenAI timeout error: %s", e)
            raise LLMTimeoutError("OpenAI provider request timed out") from e
        except APIConnectionError as e:
            logger.error("OpenAI connection error: %s", e)
            raise LLMProviderConnectionError("Could not connect to OpenAI services") from e
        except APIStatusError as e:
            logger.error("OpenAI API status error: %s", e)
            raise LLMError(f"OpenAI error status {e.status_code}: {e.message}", status_code=e.status_code) from e
        except OpenAIError as e:
            logger.error("OpenAI SDK general error: %s", e)
            raise LLMError(f"OpenAI general error: {str(e)}") from e
        except Exception as e:
            logger.error("Unexpected error in OpenAI provider: %s", e)
            raise LLMError(f"Unexpected OpenAI provider error: {str(e)}") from e
