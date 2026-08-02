"""
Tests for llm_service.py — provider implementations, timeout handling,
context limits, and factory function.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from app.services.llm_service import (
    get_llm_provider,
    OllamaProvider,
    AnthropicProvider,
    OpenAIProvider,
    ProviderUnavailableError,
    InvalidAPIKeyError,
    ModelNotFoundError,
    LLMTimeoutError,
    LLMError,
)


# ---------------------------------------------------------------------------
# OllamaProvider — success
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_ollama_provider_success():
    provider = OllamaProvider(model="llama3", base_url="http://localhost:11434")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "message": {"role": "assistant", "content": "Hello from Ollama!"}
    }

    with patch("httpx.AsyncClient.post", return_value=mock_response) as mock_post:
        result = await provider.generate([{"role": "user", "content": "Hi"}])
        assert result == "Hello from Ollama!"
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == "http://localhost:11434/api/chat"
        assert kwargs["json"]["model"] == "llama3"
        assert kwargs["json"]["stream"] is False


# ---------------------------------------------------------------------------
# OllamaProvider — configurable timeouts
# ---------------------------------------------------------------------------

def test_ollama_provider_uses_configurable_timeout():
    """Provider stores timeout values from constructor arguments."""
    provider = OllamaProvider(model="llama3", timeout=300, connect_timeout=10)
    assert provider.timeout == 300
    assert provider.connect_timeout == 10


def test_ollama_provider_httpx_timeout_object():
    """_build_http_timeout returns an httpx.Timeout with correct split values."""
    provider = OllamaProvider(model="llama3", timeout=300, connect_timeout=10)
    t = provider._build_http_timeout()
    assert isinstance(t, httpx.Timeout)
    assert t.connect == 10.0
    assert t.read == 300.0
    assert t.write == 300.0


def test_ollama_provider_respects_settings(monkeypatch):
    """When no explicit timeout is given, values come from settings."""
    monkeypatch.setattr("app.services.llm_service.settings.OLLAMA_TIMEOUT", 240)
    monkeypatch.setattr("app.services.llm_service.settings.OLLAMA_CONNECT_TIMEOUT", 5)
    provider = OllamaProvider(model="llama3")
    assert provider.timeout == 240
    assert provider.connect_timeout == 5


# ---------------------------------------------------------------------------
# OllamaProvider — error cases
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_ollama_provider_unavailable():
    provider = OllamaProvider(model="llama3")
    with patch("httpx.AsyncClient.post", side_effect=httpx.ConnectError("Connection refused")):
        with pytest.raises(ProviderUnavailableError, match="Cannot connect to Ollama"):
            await provider.generate([{"role": "user", "content": "Hi"}])


@pytest.mark.anyio
async def test_ollama_provider_connect_timeout():
    """httpx.ConnectTimeout → ProviderUnavailableError (not LLMTimeoutError)."""
    provider = OllamaProvider(model="llama3")
    with patch("httpx.AsyncClient.post", side_effect=httpx.ConnectTimeout("Timed out")):
        with pytest.raises(ProviderUnavailableError, match="Timed out connecting"):
            await provider.generate([{"role": "user", "content": "Hi"}])


@pytest.mark.anyio
async def test_ollama_provider_read_timeout():
    """httpx.ReadTimeout → LLMTimeoutError (generation ran too long)."""
    provider = OllamaProvider(model="llama3", timeout=60)
    with patch("httpx.AsyncClient.post", side_effect=httpx.ReadTimeout("Read timed out")):
        with pytest.raises(LLMTimeoutError, match="generation timed out"):
            await provider.generate([{"role": "user", "content": "Hi"}])


@pytest.mark.anyio
async def test_ollama_provider_general_timeout():
    """Generic httpx.TimeoutException → LLMTimeoutError."""
    provider = OllamaProvider(model="llama3")
    with patch("httpx.AsyncClient.post", side_effect=httpx.TimeoutException("Timeout")):
        with pytest.raises(LLMTimeoutError):
            await provider.generate([{"role": "user", "content": "Hi"}])


@pytest.mark.anyio
async def test_ollama_model_not_found():
    provider = OllamaProvider(model="llama3")
    mock_response = MagicMock()
    mock_response.status_code = 404
    with patch("httpx.AsyncClient.post", return_value=mock_response):
        with pytest.raises(ModelNotFoundError):
            await provider.generate([{"role": "user", "content": "Hi"}])


@pytest.mark.anyio
async def test_ollama_non_200_response():
    """Non-200 / non-404 status codes → LLMError."""
    provider = OllamaProvider(model="llama3")
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal server error"
    with patch("httpx.AsyncClient.post", return_value=mock_response):
        with pytest.raises(LLMError, match="Ollama error 500"):
            await provider.generate([{"role": "user", "content": "Hi"}])


# ---------------------------------------------------------------------------
# OllamaProvider — system prompt handling
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_ollama_prepends_system_prompt():
    """System prompt is prepended as a system role message."""
    provider = OllamaProvider(model="llama3")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"message": {"content": "ok"}}

    with patch("httpx.AsyncClient.post", return_value=mock_response) as mock_post:
        await provider.generate(
            [{"role": "user", "content": "hello"}],
            system_prompt="You are helpful.",
        )
        sent_messages = mock_post.call_args[1]["json"]["messages"]
        assert sent_messages[0]["role"] == "system"
        assert sent_messages[0]["content"] == "You are helpful."
        assert sent_messages[1]["role"] == "user"


# ---------------------------------------------------------------------------
# Factory function
# ---------------------------------------------------------------------------

def test_get_llm_provider_ollama(monkeypatch):
    monkeypatch.setattr("app.services.llm_service.settings.LLM_PROVIDER", "ollama")
    monkeypatch.setattr("app.services.llm_service.settings.OLLAMA_MODEL", "llama3.1:8b")
    provider = get_llm_provider()
    assert isinstance(provider, OllamaProvider)
    assert provider.model == "llama3.1:8b"


def test_get_llm_provider_unknown_raises(monkeypatch):
    monkeypatch.setattr("app.services.llm_service.settings.LLM_PROVIDER", "fakeprovider")
    with pytest.raises(ValueError, match="Unknown LLM provider"):
        get_llm_provider()


def test_get_llm_provider_openai_without_key_raises(monkeypatch):
    """OpenAIProvider raises InvalidAPIKeyError when key is placeholder."""
    monkeypatch.setattr("app.services.llm_service.settings.LLM_PROVIDER", "openai")
    monkeypatch.setattr(
        "app.services.llm_service.settings.OPENAI_API_KEY", "your-openai-api-key-here"
    )
    with pytest.raises(InvalidAPIKeyError):
        get_llm_provider()


# ---------------------------------------------------------------------------
# GeminiProvider tests
# ---------------------------------------------------------------------------

from app.services.llm_service import GeminiProvider


def test_gemini_provider_missing_key():
    with pytest.raises(InvalidAPIKeyError, match="Gemini API key is not configured"):
        GeminiProvider(api_key="")


@pytest.mark.anyio
async def test_gemini_provider_success():
    provider = GeminiProvider(api_key="valid-test-key", model="gemini-1.5-flash")
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": "Hello from Gemini!"}]
                }
            }
        ]
    }
    with patch("httpx.AsyncClient.post", return_value=mock_response) as mock_post:
        res = await provider.generate([{"role": "user", "content": "Hi"}], system_prompt="Be helpful")
        assert res == "Hello from Gemini!"
        mock_post.assert_called_once()
        url = mock_post.call_args[0][0]
        assert "generativelanguage.googleapis.com" in url
        assert "gemini-1.5-flash" in url


def test_get_llm_provider_gemini(monkeypatch):
    monkeypatch.setattr("app.services.llm_service.settings.LLM_PROVIDER", "gemini")
    monkeypatch.setattr("app.services.llm_service.settings.GEMINI_API_KEY", "test-key-123")
    provider = get_llm_provider()
    assert isinstance(provider, GeminiProvider)
    assert provider.model == "gemini-1.5-flash"


def test_get_llm_provider_anthropic(monkeypatch):
    monkeypatch.setattr("app.services.llm_service.settings.LLM_PROVIDER", "anthropic")
    monkeypatch.setattr("app.services.llm_service.settings.ANTHROPIC_API_KEY", "test-key-456")
    provider = get_llm_provider()
    assert isinstance(provider, AnthropicProvider)
    assert provider.model == "claude-3-5-sonnet-20241022"


def test_anthropic_provider_missing_key():
    with pytest.raises(InvalidAPIKeyError, match="Anthropic API key is not configured"):
        AnthropicProvider(api_key="")


@pytest.mark.anyio
async def test_provider_specific_token_parameters():
    """Verify max_tokens parameter mapping for Gemini and Anthropic."""
    gemini_p = GeminiProvider(api_key="key-123", model="gemini-1.5-flash")
    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.json.return_value = {"candidates": [{"content": {"parts": [{"text": "ok"}]}}]}
    with patch("httpx.AsyncClient.post", return_value=mock_res) as mock_post:
        await gemini_p.generate([{"role": "user", "content": "hi"}], max_tokens=500)
        json_payload = mock_post.call_args[1]["json"]
        assert json_payload["generationConfig"]["maxOutputTokens"] == 500


