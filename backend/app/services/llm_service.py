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


class RateLimitError(LLMError):
    """Raised when the LLM provider rate limit is exceeded."""
    pass


class TokenLimitExceededError(LLMError):
    """Raised when prompt or output token limit is exceeded."""
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
    """Local Ollama inference provider."""

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
            "[LLM] OllamaProvider initialised | model=%s | base_url=%s",
            self.model,
            self.base_url,
        )

    def _build_http_timeout(self) -> httpx.Timeout:
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
        formatted_messages: List[Dict[str, str]] = []
        if system_prompt:
            formatted_messages.append({"role": "system", "content": system_prompt})
        formatted_messages.extend(messages)

        prompt_chars = sum(len(m.get("content", "")) for m in formatted_messages)

        options = dict(kwargs.get("options", {}))
        if "max_tokens" in kwargs and "num_predict" not in options:
            options["num_predict"] = kwargs["max_tokens"]

        logger.info(
            "[LLM] Ollama generate | model=%s | messages=%d | prompt_chars≈%d",
            self.model,
            len(formatted_messages),
            prompt_chars,
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
                        "options": options,
                    },
                )
            except httpx.ConnectError as e:
                raise ProviderUnavailableError(
                    f"Cannot connect to Ollama at {self.base_url}. Make sure Ollama is running (`ollama serve`)."
                ) from e
            except httpx.ConnectTimeout as e:
                raise ProviderUnavailableError(
                    f"Timed out connecting to Ollama at {self.base_url}."
                ) from e
            except httpx.ReadTimeout as e:
                raise LLMTimeoutError("Ollama generation timed out.") from e
            except httpx.TimeoutException as e:
                raise LLMTimeoutError("Ollama request timed out.") from e
            except Exception as e:
                raise LLMError(f"Error communicating with Ollama: {str(e)}") from e

        elapsed = time.monotonic() - start_time
        logger.info("[LLM] Ollama responded in %.1fs (status=%d)", elapsed, response.status_code)

        if response.status_code == 404:
            raise ModelNotFoundError(f"Model '{self.model}' not found on local Ollama server.")
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
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        self.model = model or getattr(settings, "ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
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
        prompt_chars = 0
        try:
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

            max_tokens = kwargs.get("max_tokens") or kwargs.get("options", {}).get("num_predict", 1000)

            start_time = time.monotonic()
            response = await self.client.messages.create(
                model=self.model,
                messages=anthropic_messages,
                system=system_prompt or "",
                max_tokens=max_tokens,
                timeout=60.0,
            )
            elapsed = time.monotonic() - start_time
            logger.info("[LLM] Anthropic responded in %.1fs", elapsed)
            return response.content[0].text

        except Exception as e:
            err_msg = str(e).lower()
            if "api_key" in err_msg or "unauthorized" in err_msg or "authentication" in err_msg or "401" in err_msg or "403" in err_msg:
                raise InvalidAPIKeyError("Anthropic API key is invalid or not configured.") from e
            elif "rate" in err_msg or "429" in err_msg:
                raise RateLimitError("Anthropic rate limit exceeded. Please try again later.") from e
            elif "token" in err_msg or "context_length" in err_msg or "maximum context" in err_msg or "too long" in err_msg:
                raise TokenLimitExceededError(f"Anthropic token limit exceeded (prompt size ~{prompt_chars} chars).") from e
            elif "not found" in err_msg or "model" in err_msg:
                raise ModelNotFoundError(f"Anthropic model '{self.model}' not found or unavailable.") from e
            elif "timeout" in err_msg or "time out" in err_msg:
                raise LLMTimeoutError("Anthropic request timed out.") from e
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
                raise InvalidAPIKeyError("OpenAI API key is invalid or not configured.") from e
            elif "not_found" in err_msg or "model" in err_msg:
                raise ModelNotFoundError(f"OpenAI model '{self.model}' not found or unavailable.") from e
            elif "timeout" in err_msg or "time out" in err_msg:
                raise LLMTimeoutError("OpenAI request timed out.") from e
            else:
                raise LLMError(f"OpenAI service error: {str(e)}") from e


# ---------------------------------------------------------------------------
# Gemini provider
# ---------------------------------------------------------------------------

class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or getattr(settings, "GEMINI_MODEL", "gemini-1.5-flash")
        if not self.api_key or self.api_key == "your-gemini-api-key-here":
            raise InvalidAPIKeyError("Gemini API key is not configured.")
        logger.info("[LLM] GeminiProvider initialised | model=%s", self.model)

    async def generate(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key,
        }

        contents = []
        for msg in messages:
            role = msg.get("role", "user")
            if role == "system":
                if not system_prompt:
                    system_prompt = msg.get("content", "")
                continue
            gemini_role = "model" if role == "assistant" else "user"
            contents.append({
                "role": gemini_role,
                "parts": [{"text": msg.get("content", "")}],
            })

        payload: Dict[str, Any] = {"contents": contents}
        if system_prompt:
            payload["system_instruction"] = {
                "parts": [{"text": system_prompt}]
            }

        generation_config = {}
        max_tokens = kwargs.get("max_tokens") or kwargs.get("options", {}).get("num_predict")
        if max_tokens:
            generation_config["maxOutputTokens"] = max_tokens

        if generation_config:
            payload["generationConfig"] = generation_config

        prompt_chars = sum(len(m.get("content", "")) for m in messages)
        if system_prompt:
            prompt_chars += len(system_prompt)
        logger.info(
            "[LLM] Gemini generate | model=%s | messages=%d | prompt_chars≈%d",
            self.model,
            len(contents),
            prompt_chars,
        )

        start_time = time.monotonic()
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(url, headers=headers, json=payload)
            except httpx.ConnectError as e:
                raise ProviderUnavailableError("Cannot connect to Gemini API.") from e
            except httpx.TimeoutException as e:
                raise LLMTimeoutError("Gemini request timed out.") from e
            except Exception as e:
                raise LLMError(f"Error communicating with Gemini: {str(e)}") from e

        elapsed = time.monotonic() - start_time
        logger.info("[LLM] Gemini responded in %.1fs (status=%d)", elapsed, response.status_code)

        if response.status_code in (401, 403):
            raise InvalidAPIKeyError("Gemini API key is invalid or unauthorized. Please check your GEMINI_API_KEY.")
        elif response.status_code == 429:
            raise RateLimitError("Gemini rate limit exceeded. Please try again later.")
        elif response.status_code == 404:
            raise ModelNotFoundError(f"Gemini model '{self.model}' not found.")
        elif response.status_code != 200:
            err_text = response.text.lower()
            if "api_key" in err_text or "unauthorized" in err_text or "invalid" in err_text:
                raise InvalidAPIKeyError("Gemini request failed due to invalid API key configuration.")
            elif "token" in err_text or "resource_exhausted" in err_text or "quota" in err_text:
                raise TokenLimitExceededError(f"Gemini token limit or quota exceeded (prompt size ~{prompt_chars} chars).")
            raise LLMError(f"Gemini API error (status {response.status_code}).")

        try:
            res_json = response.json()
            candidates = res_json.get("candidates", [])
            if not candidates:
                raise LLMError("Gemini returned no response candidates.")
            parts = candidates[0].get("content", {}).get("parts", [])
            return "".join(part.get("text", "") for part in parts)
        except LLMError:
            raise
        except Exception as e:
            raise LLMError(f"Failed to parse Gemini response: {str(e)}") from e


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

ALLOWED_PROVIDERS = {"ollama", "gemini", "anthropic", "openai"}

def get_llm_provider(provider_name: str = None, model_name: str = None) -> LLMProvider:
    """Factory — return the configured LLM provider instance."""
    p_name = (provider_name or settings.LLM_PROVIDER).lower()
    logger.info("[LLM] Resolving provider: %s", p_name)

    if p_name not in ALLOWED_PROVIDERS:
        raise ValueError(f"Unknown LLM provider: '{p_name}'. Expected: ollama | gemini | anthropic")

    if p_name == "ollama":
        return OllamaProvider(model=model_name or settings.OLLAMA_MODEL)
    elif p_name == "gemini":
        return GeminiProvider(model=model_name or getattr(settings, "GEMINI_MODEL", "gemini-1.5-flash"))
    elif p_name == "anthropic":
        return AnthropicProvider(model=model_name or getattr(settings, "ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"))
    elif p_name == "openai":
        return OpenAIProvider(model=model_name or "gpt-4o")
    else:
        raise ValueError(f"Unknown LLM provider: '{p_name}'. Expected: ollama | gemini | anthropic")


