"""
LLM service — provider implementations and factory.

Providers
---------
- OllamaProvider   : local Ollama inference (default)
- AnthropicProvider: Anthropic Claude via API
- OpenAIProvider   : OpenAI ChatGPT via API

Timeout strategy (Ollama)
-------------------------
Local inference on a consumer-grade GPU / CPU can take 60-240 s for
llama3.1:8b. We therefore use a *split* httpx.Timeout so that:
  - connect_timeout  → short (fail fast if Ollama isn't running)
  - read/write/pool  → long (give the model time to generate)

Both values are driven by environment variables so they can be tuned
without touching source code:
  OLLAMA_CONNECT_TIMEOUT=10   (seconds, default)
  OLLAMA_TIMEOUT=300          (seconds, default)
"""

import time
import httpx
import logging
from typing import List, Dict, Any, Optional

from app.core.config import settings
from anthropic import AsyncAnthropic
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------

class LLMError(Exception):
    """Base class for all LLM service errors."""
    pass


class ProviderUnavailableError(LLMError):
    """Raised when the LLM provider cannot be reached (e.g. Ollama offline, API down)."""
    pass


class InvalidAPIKeyError(LLMError):
    """Raised when the provider rejects the API key."""
    pass


class ModelNotFoundError(LLMError):
    """Raised when the requested model is not installed or available on the provider."""
    pass


class LLMTimeoutError(LLMError):
    """Raised when the LLM request times out."""
    pass


# ---------------------------------------------------------------------------
# Base provider
# ---------------------------------------------------------------------------

class LLMProvider:
    """Interface for LLM providers."""

    async def generate(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> str:
        raise NotImplementedError()


# ---------------------------------------------------------------------------
# Ollama provider
# ---------------------------------------------------------------------------

class OllamaProvider(LLMProvider):
    """Local Ollama inference provider.

    Timeout handling
    ~~~~~~~~~~~~~~~~
    Uses two separate timeouts:
      - connect_timeout : ``settings.OLLAMA_CONNECT_TIMEOUT`` (default 10 s)
      - read_timeout    : ``settings.OLLAMA_TIMEOUT`` (default 300 s)

    Both can be overridden via environment variables without code changes.
    """

    def __init__(
        self,
        model: str = None,
        base_url: str = None,
        timeout: int = None,
        connect_timeout: int = None,
    ):
        self.model = model or settings.OLLAMA_MODEL
        self.base_url = base_url or settings.OLLAMA_BASE_URL
        self.timeout = timeout if timeout is not None else settings.OLLAMA_TIMEOUT
        self.connect_timeout = (
            connect_timeout if connect_timeout is not None else settings.OLLAMA_CONNECT_TIMEOUT
        )

        logger.info(
            "[LLM] OllamaProvider initialised | model=%s | base_url=%s | "
            "connect_timeout=%ds | generation_timeout=%ds",
            self.model,
            self.base_url,
            self.connect_timeout,
            self.timeout,
        )

    def _build_http_timeout(self) -> httpx.Timeout:
        """Return an httpx.Timeout with separate connect and read limits."""
        return httpx.Timeout(
            connect=float(self.connect_timeout),
            read=float(self.timeout),
            write=float(self.timeout),
            pool=float(self.connect_timeout),
        )

    async def generate(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> str:
        # Build the final message list, prepending system prompt if provided
        formatted_messages: List[Dict[str, str]] = []
        if system_prompt:
            formatted_messages.append({"role": "system", "content": system_prompt})
        formatted_messages.extend(messages)

        # Compute approximate prompt size for logging
        prompt_chars = sum(len(m.get("content", "")) for m in formatted_messages)
        prompt_words = prompt_chars // 5  # rough estimate

        logger.info(
            "[LLM] Ollama generate | model=%s | messages=%d | "
            "prompt_chars≈%d (~%d words) | timeout=%ds",
            self.model,
            len(formatted_messages),
            prompt_chars,
            prompt_words,
            self.timeout,
        )

        timeout = self._build_http_timeout()
        start_time = time.monotonic()

        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": self.model,
                        "messages": formatted_messages,
                        "stream": False,
                        "options": kwargs.get("options", {}),
                    },
                )
            except httpx.ConnectError as e:
                logger.error(
                    "[LLM] Ollama connect error (base_url=%s): %s", self.base_url, e
                )
                raise ProviderUnavailableError(
                    f"Cannot connect to Ollama at {self.base_url}. "
                    "Make sure Ollama is running (`ollama serve`)."
                ) from e
            except httpx.ConnectTimeout as e:
                logger.error(
                    "[LLM] Ollama connect timed out after %ds: %s",
                    self.connect_timeout,
                    e,
                )
                raise ProviderUnavailableError(
                    f"Timed out connecting to Ollama at {self.base_url} "
                    f"(connect_timeout={self.connect_timeout}s). "
                    "Is Ollama running?"
                ) from e
            except httpx.ReadTimeout as e:
                elapsed = time.monotonic() - start_time
                logger.error(
                    "[LLM] Ollama generation timed out after %.1fs "
                    "(generation_timeout=%ds, prompt_chars≈%d)",
                    elapsed,
                    self.timeout,
                    prompt_chars,
                )
                raise LLMTimeoutError(
                    f"Ollama generation timed out after {elapsed:.0f}s "
                    f"(limit={self.timeout}s). "
                    "Consider increasing OLLAMA_TIMEOUT or reducing context size."
                ) from e
            except httpx.TimeoutException as e:
                elapsed = time.monotonic() - start_time
                logger.error(
                    "[LLM] Ollama request timed out after %.1fs: %s", elapsed, e
                )
                raise LLMTimeoutError(
                    f"Ollama request timed out after {elapsed:.0f}s. "
                    f"Increase OLLAMA_TIMEOUT (currently {self.timeout}s) if needed."
                ) from e
            except Exception as e:
                logger.error("[LLM] Unexpected error communicating with Ollama: %s", e)
                raise LLMError(f"Error communicating with Ollama: {str(e)}") from e

        elapsed = time.monotonic() - start_time
        logger.info("[LLM] Ollama responded in %.1fs (status=%d)", elapsed, response.status_code)

        if response.status_code == 404:
            raise ModelNotFoundError(
                f"Model '{self.model}' not found on local Ollama server. "
                f"Pull it first: `ollama pull {self.model}`."
            )
        elif response.status_code != 200:
            raise LLMError(f"Ollama error {response.status_code}: {response.text}")

        try:
            result = response.json()
            return result["message"]["content"]
        except Exception as e:
            raise LLMError(f"Failed to parse Ollama response: {str(e)}") from e


# ---------------------------------------------------------------------------
# Anthropic provider
# ---------------------------------------------------------------------------

class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str = None, model: str = "claude-3-5-sonnet-20241022"):
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        self.model = model
        if not self.api_key or self.api_key == "your-anthropic-api-key-here":
            raise InvalidAPIKeyError("Anthropic API key is not configured.")
        self.client = AsyncAnthropic(api_key=self.api_key)
        logger.info("[LLM] AnthropicProvider initialised | model=%s", self.model)

    async def generate(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> str:
        try:
            # Anthropic does not allow "system" inside the messages list
            anthropic_messages = []
            for msg in messages:
                role = msg["role"]
                if role == "system":
                    if not system_prompt:
                        system_prompt = msg["content"]
                    continue
                anthropic_messages.append({"role": role, "content": msg["content"]})

            prompt_chars = sum(len(m.get("content", "")) for m in anthropic_messages)
            if system_prompt:
                prompt_chars += len(system_prompt)
            logger.info(
                "[LLM] Anthropic generate | model=%s | messages=%d | prompt_chars≈%d",
                self.model,
                len(anthropic_messages),
                prompt_chars,
            )

            start_time = time.monotonic()
            response = await self.client.messages.create(
                model=self.model,
                messages=anthropic_messages,
                system=system_prompt or "",
                max_tokens=kwargs.get("max_tokens", 4000),
                timeout=60.0,
            )
            elapsed = time.monotonic() - start_time
            logger.info("[LLM] Anthropic responded in %.1fs", elapsed)
            return response.content[0].text

        except Exception as e:
            err_msg = str(e).lower()
            if "api_key" in err_msg or "unauthorized" in err_msg or "authentication" in err_msg:
                raise InvalidAPIKeyError(f"Anthropic API key is invalid: {str(e)}") from e
            elif "not found" in err_msg or "model" in err_msg:
                raise ModelNotFoundError(
                    f"Anthropic model {self.model} not found or unavailable: {str(e)}"
                ) from e
            elif "timeout" in err_msg or "time out" in err_msg:
                raise LLMTimeoutError(f"Anthropic request timed out: {str(e)}") from e
            else:
                raise LLMError(f"Anthropic service error: {str(e)}") from e


# ---------------------------------------------------------------------------
# OpenAI provider
# ---------------------------------------------------------------------------

class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str = None, model: str = "gpt-4o"):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model
        if not self.api_key or self.api_key == "your-openai-api-key-here":
            raise InvalidAPIKeyError("OpenAI API key is not configured.")
        self.client = AsyncOpenAI(api_key=self.api_key)
        logger.info("[LLM] OpenAIProvider initialised | model=%s", self.model)

    async def generate(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> str:
        formatted_messages = []
        if system_prompt:
            formatted_messages.append({"role": "system", "content": system_prompt})
        formatted_messages.extend(messages)

        prompt_chars = sum(len(m.get("content", "")) for m in formatted_messages)
        logger.info(
            "[LLM] OpenAI generate | model=%s | messages=%d | prompt_chars≈%d",
            self.model,
            len(formatted_messages),
            prompt_chars,
        )

        try:
            start_time = time.monotonic()
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=formatted_messages,
                timeout=60.0,
            )
            elapsed = time.monotonic() - start_time
            logger.info("[LLM] OpenAI responded in %.1fs", elapsed)
            return response.choices[0].message.content

        except Exception as e:
            err_msg = str(e).lower()
            if "api_key" in err_msg or "unauthorized" in err_msg or "authentication" in err_msg:
                raise InvalidAPIKeyError(f"OpenAI API key is invalid: {str(e)}") from e
            elif "not_found" in err_msg or "model" in err_msg:
                raise ModelNotFoundError(
                    f"OpenAI model {self.model} not found or unavailable: {str(e)}"
                ) from e
            elif "timeout" in err_msg or "time out" in err_msg:
                raise LLMTimeoutError(f"OpenAI request timed out: {str(e)}") from e
            else:
                raise LLMError(f"OpenAI service error: {str(e)}") from e


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def get_llm_provider(provider_name: str = None, model_name: str = None) -> LLMProvider:
    """Factory — return the configured LLM provider instance."""
    p_name = (provider_name or settings.LLM_PROVIDER).lower()
    logger.info("[LLM] Resolving provider: %s", p_name)

    if p_name == "ollama":
        provider = OllamaProvider(model=model_name or settings.OLLAMA_MODEL)
        return provider
    elif p_name == "anthropic":
        return AnthropicProvider(model=model_name or "claude-3-5-sonnet-20241022")
    elif p_name == "openai":
        return OpenAIProvider(model=model_name or "gpt-4o")
    else:
        raise ValueError(f"Unknown LLM provider: '{p_name}'. Expected: ollama | anthropic | openai")
