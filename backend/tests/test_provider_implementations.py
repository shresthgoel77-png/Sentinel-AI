# pyrefly: ignore [missing-import]
"""Unit tests for provider implementations and the router's exception handling."""

import sys
import os
import asyncio

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from exceptions.provider_exceptions import (
    ProviderTimeoutError,
    ProviderRateLimitError,
    ProviderAuthenticationError,
    ProviderAPIError,
    ProviderConfigurationError,
    SentinelProviderError,
)
from providers.openai import OpenAIProvider
from providers.gemini import GeminiProvider
from providers.anthropic import AnthropicProvider
from providers.router import ProviderRouter

# ---------------------------------------------------------------------------
# OpenAI provider
# ---------------------------------------------------------------------------


class TestOpenAIProvider:
    @pytest.mark.asyncio
    async def test_successful_completion(self):
        """A successful OpenAI call returns the mapped response."""
        provider = OpenAIProvider()
        request = MagicMock()
        request.model_dump.return_value = {"model": "gpt-4", "messages": []}

        mock_response = MagicMock()
        mock_response.model_dump.return_value = {"id": "chat-1"}

        with patch("providers.openai.AsyncOpenAI") as mock_client_cls:
            mock_client = mock_client_cls.return_value
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

            result = await provider.generate_completion(request, "test-key")

        assert result == {"id": "chat-1"}

    @pytest.mark.asyncio
    async def test_authentication_error_propagates(self):
        """OpenAI AuthenticationError is wrapped as ProviderAuthenticationError."""
        from openai import AuthenticationError
        import httpx

        provider = OpenAIProvider()
        request = MagicMock()
        request.model_dump.return_value = {"model": "gpt-4", "messages": []}

        req = httpx.Request("POST", "http://test")
        resp = httpx.Response(401, request=req)
        original = AuthenticationError("bad key", response=resp, body=None)

        with patch("providers.openai.AsyncOpenAI") as mock_client_cls:
            mock_client = mock_client_cls.return_value
            mock_client.chat.completions.create = AsyncMock(side_effect=original)

            with pytest.raises(ProviderAuthenticationError) as exc_info:
                await provider.generate_completion(request, "test-key")

        assert exc_info.value.__cause__ is original

    @pytest.mark.asyncio
    async def test_rate_limit_error_propagates(self):
        """OpenAI RateLimitError is wrapped as ProviderRateLimitError."""
        from openai import RateLimitError
        import httpx

        provider = OpenAIProvider()
        request = MagicMock()
        request.model_dump.return_value = {"model": "gpt-4", "messages": []}

        req = httpx.Request("POST", "http://test")
        resp = httpx.Response(429, request=req)
        original = RateLimitError("rate limited", response=resp, body=None)

        with patch("providers.openai.AsyncOpenAI") as mock_client_cls:
            mock_client = mock_client_cls.return_value
            mock_client.chat.completions.create = AsyncMock(side_effect=original)

            with pytest.raises(ProviderRateLimitError) as exc_info:
                await provider.generate_completion(request, "test-key")

        assert exc_info.value.__cause__ is original

    @pytest.mark.asyncio
    async def test_timeout_error_propagates(self):
        """OpenAI APITimeoutError is wrapped as ProviderTimeoutError."""
        from openai import APITimeoutError
        import httpx

        provider = OpenAIProvider()
        request = MagicMock()
        request.model_dump.return_value = {"model": "gpt-4", "messages": []}

        req = httpx.Request("POST", "http://test")
        original = APITimeoutError(request=req)

        with patch("providers.openai.AsyncOpenAI") as mock_client_cls:
            mock_client = mock_client_cls.return_value
            mock_client.chat.completions.create = AsyncMock(side_effect=original)

            with pytest.raises(ProviderTimeoutError) as exc_info:
                await provider.generate_completion(request, "test-key")

        assert exc_info.value.__cause__ is original

    @pytest.mark.asyncio
    async def test_api_error_propagates(self):
        """OpenAI APIError is wrapped as ProviderAPIError."""
        from openai import APIError
        import httpx

        provider = OpenAIProvider()
        request = MagicMock()
        request.model_dump.return_value = {"model": "gpt-4", "messages": []}

        req = httpx.Request("POST", "http://test")
        original = APIError("server error", request=req, body=None)

        with patch("providers.openai.AsyncOpenAI") as mock_client_cls:
            mock_client = mock_client_cls.return_value
            mock_client.chat.completions.create = AsyncMock(side_effect=original)

            with pytest.raises(ProviderAPIError) as exc_info:
                await provider.generate_completion(request, "test-key")

        assert exc_info.value.__cause__ is original


# ---------------------------------------------------------------------------
# Gemini provider
# ---------------------------------------------------------------------------


class TestGeminiProvider:
    @pytest.mark.asyncio
    async def test_successful_completion(self):
        """A successful Gemini call returns the mapped OpenAI-style response."""
        provider = GeminiProvider()
        request = MagicMock()
        request.model = "gemini-pro"
        request.messages = [
            MagicMock(role="system", content="You are helpful"),
            MagicMock(role="user", content="Hello"),
        ]
        request.temperature = 0.5
        request.max_tokens = 100

        mock_response = MagicMock()
        mock_response.text = "Hello there"
        mock_response.usage_metadata = MagicMock(
            prompt_token_count=10,
            candidates_token_count=5,
            total_token_count=15,
        )

        with patch("providers.gemini.genai.Client") as mock_client_cls:
            mock_client = mock_client_cls.return_value
            mock_client.aio.models.generate_content = AsyncMock(
                return_value=mock_response
            )

            result = await provider.generate_completion(request, "test-key")

        assert result["choices"][0]["message"]["content"] == "Hello there"
        assert result["usage"]["total_tokens"] == 15

    @pytest.mark.asyncio
    async def test_rate_limit_error_propagates(self):
        """Gemini 429 error is wrapped as ProviderRateLimitError."""
        from google.genai import errors

        provider = GeminiProvider()
        request = MagicMock()
        request.model = "gemini-pro"
        request.messages = [MagicMock(role="user", content="Hello")]
        request.temperature = None
        request.max_tokens = None

        original = errors.APIError(429, {"error": {"message": "rate limited"}})

        with patch("providers.gemini.genai.Client") as mock_client_cls:
            mock_client = mock_client_cls.return_value
            mock_client.aio.models.generate_content = AsyncMock(side_effect=original)

            with pytest.raises(ProviderRateLimitError) as exc_info:
                await provider.generate_completion(request, "test-key")

        assert exc_info.value.__cause__ is original

    @pytest.mark.asyncio
    async def test_authentication_error_propagates(self):
        """Gemini 401 error is wrapped as ProviderAuthenticationError."""
        from google.genai import errors

        provider = GeminiProvider()
        request = MagicMock()
        request.model = "gemini-pro"
        request.messages = [MagicMock(role="user", content="Hello")]
        request.temperature = None
        request.max_tokens = None

        original = errors.APIError(401, {"error": {"message": "unauthorized"}})

        with patch("providers.gemini.genai.Client") as mock_client_cls:
            mock_client = mock_client_cls.return_value
            mock_client.aio.models.generate_content = AsyncMock(side_effect=original)

            with pytest.raises(ProviderAuthenticationError) as exc_info:
                await provider.generate_completion(request, "test-key")

        assert exc_info.value.__cause__ is original

    @pytest.mark.asyncio
    async def test_api_error_propagates(self):
        """Gemini 500 error is wrapped as ProviderAPIError."""
        from google.genai import errors

        provider = GeminiProvider()
        request = MagicMock()
        request.model = "gemini-pro"
        request.messages = [MagicMock(role="user", content="Hello")]
        request.temperature = None
        request.max_tokens = None

        original = errors.APIError(500, {"error": {"message": "server error"}})

        with patch("providers.gemini.genai.Client") as mock_client_cls:
            mock_client = mock_client_cls.return_value
            mock_client.aio.models.generate_content = AsyncMock(side_effect=original)

            with pytest.raises(ProviderAPIError) as exc_info:
                await provider.generate_completion(request, "test-key")

        assert exc_info.value.__cause__ is original


# ---------------------------------------------------------------------------
# Anthropic provider
# ---------------------------------------------------------------------------


class TestAnthropicProvider:
    @pytest.mark.asyncio
    async def test_successful_completion(self):
        """A successful Anthropic call returns the mapped OpenAI-style response."""
        provider = AnthropicProvider()
        request = MagicMock()
        request.model = "claude-3"
        request.messages = [
            MagicMock(role="system", content="You are helpful"),
            MagicMock(role="user", content="Hello"),
        ]
        request.temperature = 0.5
        request.max_tokens = 100

        mock_response = MagicMock()
        mock_response.id = "msg-1"
        mock_response.model = "claude-3"
        mock_response.content = [MagicMock(text="Hello there")]
        mock_response.usage = MagicMock(input_tokens=10, output_tokens=5)

        with patch("providers.anthropic.AsyncAnthropic") as mock_client_cls:
            mock_client = mock_client_cls.return_value
            mock_client.messages.create = AsyncMock(return_value=mock_response)

            result = await provider.generate_completion(request, "test-key")

        assert result["choices"][0]["message"]["content"] == "Hello there"
        assert result["usage"]["total_tokens"] == 15

    @pytest.mark.asyncio
    async def test_authentication_error_propagates(self):
        """Anthropic AuthenticationError is wrapped as ProviderAuthenticationError."""

        # Build a fake anthropic-style error since the SDK may not be installed.
        class FakeAnthropicAuthError(Exception):
            pass

        provider = AnthropicProvider()
        request = MagicMock()
        request.model = "claude-3"
        request.messages = [MagicMock(role="user", content="Hello")]
        request.temperature = None
        request.max_tokens = None

        original = FakeAnthropicAuthError("bad key")

        import exceptions.error_mapping as em

        old = em._AnthropicAuthenticationError
        em._AnthropicAuthenticationError = FakeAnthropicAuthError
        try:
            with patch("providers.anthropic.AsyncAnthropic") as mock_client_cls:
                mock_client = mock_client_cls.return_value
                mock_client.messages.create = AsyncMock(side_effect=original)

                with pytest.raises(ProviderAuthenticationError) as exc_info:
                    await provider.generate_completion(request, "test-key")

            assert exc_info.value.__cause__ is original
        finally:
            em._AnthropicAuthenticationError = old

    @pytest.mark.asyncio
    async def test_rate_limit_error_propagates(self):
        """Anthropic RateLimitError is wrapped as ProviderRateLimitError."""

        class FakeAnthropicRateLimitError(Exception):
            pass

        provider = AnthropicProvider()
        request = MagicMock()
        request.model = "claude-3"
        request.messages = [MagicMock(role="user", content="Hello")]
        request.temperature = None
        request.max_tokens = None

        original = FakeAnthropicRateLimitError("rate limited")

        import exceptions.error_mapping as em

        old = em._AnthropicRateLimitError
        em._AnthropicRateLimitError = FakeAnthropicRateLimitError
        try:
            with patch("providers.anthropic.AsyncAnthropic") as mock_client_cls:
                mock_client = mock_client_cls.return_value
                mock_client.messages.create = AsyncMock(side_effect=original)

                with pytest.raises(ProviderRateLimitError) as exc_info:
                    await provider.generate_completion(request, "test-key")

            assert exc_info.value.__cause__ is original
        finally:
            em._AnthropicRateLimitError = old


# ---------------------------------------------------------------------------
# Router exception handling
# ---------------------------------------------------------------------------


class TestProviderRouter:
    @pytest.mark.asyncio
    async def test_timeout_falls_back(self):
        """asyncio.TimeoutError in the router triggers a fallback to the next provider."""
        router = ProviderRouter()
        request = MagicMock()
        request.model = "gpt-4"

        with patch.object(
            router.providers["openai"], "generate_completion", new_callable=AsyncMock
        ) as mock_openai, patch.object(
            router.providers["gemini"], "generate_completion", new_callable=AsyncMock
        ) as mock_gemini:
            mock_openai.side_effect = asyncio.TimeoutError()
            mock_gemini.return_value = {"id": "gemini-1"}

            result = await router.route(request, "test-key")

        mock_openai.assert_awaited_once()
        mock_gemini.assert_awaited_once()
        assert result["id"] == "gemini-1"

    @pytest.mark.asyncio
    async def test_rate_limit_falls_back(self):
        """ProviderRateLimitError in the router triggers a fallback to the next provider."""
        router = ProviderRouter()
        request = MagicMock()
        request.model = "gpt-4"

        with patch.object(
            router.providers["openai"], "generate_completion", new_callable=AsyncMock
        ) as mock_openai, patch.object(
            router.providers["gemini"], "generate_completion", new_callable=AsyncMock
        ) as mock_gemini:
            mock_openai.side_effect = ProviderRateLimitError("rate limited")
            mock_gemini.return_value = {"id": "gemini-1"}

            result = await router.route(request, "test-key")

        mock_openai.assert_awaited_once()
        mock_gemini.assert_awaited_once()
        assert result["id"] == "gemini-1"

    @pytest.mark.asyncio
    async def test_authentication_returns_401(self):
        """ProviderAuthenticationError in the router returns a 401 error response."""
        router = ProviderRouter()
        request = MagicMock()
        request.model = "gpt-4"

        with patch.object(
            router.providers["openai"], "generate_completion", new_callable=AsyncMock
        ) as mock_gen:
            mock_gen.side_effect = ProviderAuthenticationError("bad key")

            result = await router.route(request, "test-key")

        assert result["error"]["code"] == 401
        assert "authentication" in result["error"]["message"].lower()

    @pytest.mark.asyncio
    async def test_provider_timeout_falls_back(self):
        """ProviderTimeoutError in the router triggers a fallback to the next provider."""
        router = ProviderRouter()
        request = MagicMock()
        request.model = "gpt-4"

        with patch.object(
            router.providers["openai"], "generate_completion", new_callable=AsyncMock
        ) as mock_openai, patch.object(
            router.providers["gemini"], "generate_completion", new_callable=AsyncMock
        ) as mock_gemini:
            mock_openai.side_effect = ProviderTimeoutError("timed out")
            mock_gemini.return_value = {"id": "gemini-1"}

            result = await router.route(request, "test-key")

        mock_openai.assert_awaited_once()
        mock_gemini.assert_awaited_once()
        assert result["id"] == "gemini-1"

    @pytest.mark.asyncio
    async def test_api_error_falls_back(self):
        """ProviderAPIError in the router triggers a fallback to the next provider."""
        router = ProviderRouter()
        request = MagicMock()
        request.model = "gpt-4"

        with patch.object(
            router.providers["openai"], "generate_completion", new_callable=AsyncMock
        ) as mock_openai, patch.object(
            router.providers["gemini"], "generate_completion", new_callable=AsyncMock
        ) as mock_gemini:
            mock_openai.side_effect = ProviderAPIError("server error")
            mock_gemini.return_value = {"id": "gemini-1"}

            result = await router.route(request, "test-key")

        mock_openai.assert_awaited_once()
        mock_gemini.assert_awaited_once()
        assert result["id"] == "gemini-1"

    @pytest.mark.asyncio
    async def test_configuration_error_returns_500(self):
        """ProviderConfigurationError in the router returns a 500 error response."""
        router = ProviderRouter()
        request = MagicMock()
        request.model = "gpt-4"

        with patch.object(
            router.providers["openai"], "generate_completion", new_callable=AsyncMock
        ) as mock_gen:
            mock_gen.side_effect = ProviderConfigurationError("misconfigured")

            result = await router.route(request, "test-key")

        assert result["error"]["code"] == 500
        assert "configuration" in result["error"]["message"].lower()

    @pytest.mark.asyncio
    async def test_base_sentinel_error_returns_500(self):
        """Any other SentinelProviderError in the router returns a 500 error response."""
        router = ProviderRouter()
        request = MagicMock()
        request.model = "gpt-4"

        class CustomProviderError(SentinelProviderError):
            pass

        with patch.object(
            router.providers["openai"], "generate_completion", new_callable=AsyncMock
        ) as mock_gen:
            mock_gen.side_effect = CustomProviderError("custom error")

            result = await router.route(request, "test-key")

        assert result["error"]["code"] == 500
        assert "provider error" in result["error"]["message"].lower()

    @pytest.mark.asyncio
    async def test_successful_route_returns_response(self):
        """A successful route returns the provider response unchanged."""
        router = ProviderRouter()
        request = MagicMock()
        request.model = "gpt-4"

        expected = {"id": "chat-1", "choices": []}

        with patch.object(
            router.providers["openai"], "generate_completion", new_callable=AsyncMock
        ) as mock_gen:
            mock_gen.return_value = expected

            result = await router.route(request, "test-key")

        assert result == expected

    @pytest.mark.asyncio
    async def test_gpt_model_routes_to_openai(self):
        """GPT/OpenAI models route to the OpenAI provider."""
        router = ProviderRouter()
        request = MagicMock()
        request.model = "gpt-4"

        with patch.object(
            router.providers["openai"], "generate_completion", new_callable=AsyncMock
        ) as mock_openai, patch.object(
            router.providers["gemini"], "generate_completion", new_callable=AsyncMock
        ) as mock_gemini:
            mock_openai.return_value = {"id": "openai-1"}
            mock_gemini.return_value = {"id": "gemini-1"}

            result = await router.route(request, "test-key")

        mock_openai.assert_awaited_once()
        mock_gemini.assert_not_awaited()
        assert result["id"] == "openai-1"

    @pytest.mark.asyncio
    async def test_claude_model_routes_to_anthropic(self):
        """Claude models route to the Anthropic provider."""
        router = ProviderRouter()
        request = MagicMock()
        request.model = "claude-3-5-sonnet"

        with patch.object(
            router.providers["anthropic"], "generate_completion", new_callable=AsyncMock
        ) as mock_anthropic, patch.object(
            router.providers["gemini"], "generate_completion", new_callable=AsyncMock
        ) as mock_gemini:
            mock_anthropic.return_value = {"id": "anthropic-1"}
            mock_gemini.return_value = {"id": "gemini-1"}

            result = await router.route(request, "test-key")

        mock_anthropic.assert_awaited_once()
        mock_gemini.assert_not_awaited()
        assert result["id"] == "anthropic-1"

    @pytest.mark.asyncio
    async def test_default_model_routes_to_gemini(self):
        """Unknown models default to the Gemini provider."""
        router = ProviderRouter()
        request = MagicMock()
        request.model = "some-unknown-model"

        with patch.object(
            router.providers["gemini"], "generate_completion", new_callable=AsyncMock
        ) as mock_gemini:
            mock_gemini.return_value = {"id": "gemini-1"}

            result = await router.route(request, "test-key")

        mock_gemini.assert_awaited_once()
        assert result["id"] == "gemini-1"
