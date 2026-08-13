# pyrefly: ignore [missing-import]
"""Unit tests for automatic LLM provider fallback (Issue #21).

These tests exercise the router's failover behaviour using mocks only; no real
SDK calls are made.  They cover the required scenarios:

- primary provider succeeds
- timeout -> fallback succeeds
- rate limit -> fallback succeeds
- provider API error -> fallback succeeds
- authentication error -> no fallback
- configuration error -> no fallback
- all providers fail
- fallback ordering
- logging
- provider switching
"""

import sys
import os
import asyncio
from contextlib import ExitStack, contextmanager

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from exceptions.provider_exceptions import (
    ProviderTimeoutError,
    ProviderRateLimitError,
    ProviderAuthenticationError,
    ProviderAPIError,
    ProviderConfigurationError,
)
from providers.router import ProviderRouter


def _make_request(model: str = "gpt-4") -> MagicMock:
    """Build a minimal request mock with a model attribute."""
    request = MagicMock()
    request.model = model
    return request


def _patch_providers(router: ProviderRouter, **side_effects):
    """Context manager that patches every provider's generate_completion.

    ``side_effects`` maps provider names to either a return value, an exception,
    or a list of values for sequential calls.  Providers not listed are patched
    with a default AsyncMock.  The yielded dict maps provider names to their
    patched mocks.  All patches are torn down when the context exits.
    """

    @contextmanager
    def _manager():
        with ExitStack() as stack:
            mocks = {}
            for name in router.providers:
                patcher = patch.object(
                    router.providers[name],
                    "generate_completion",
                    new_callable=AsyncMock,
                )
                mocks[name] = stack.enter_context(patcher)

            for name, effect in side_effects.items():
                if isinstance(effect, list):
                    mocks[name].side_effect = effect
                elif isinstance(effect, BaseException):
                    mocks[name].side_effect = effect
                else:
                    mocks[name].return_value = effect

            yield mocks

    return _manager()


class TestPrimaryProviderSucceeds:
    @pytest.mark.asyncio
    async def test_openai_succeeds_no_fallback(self):
        """When the primary provider succeeds, no fallback is attempted."""
        router = ProviderRouter()
        request = _make_request("gpt-4")
        expected = {"id": "openai-1"}

        with _patch_providers(
            router,
            openai=expected,
            gemini={"id": "gemini-1"},
            anthropic={"id": "anthropic-1"},
        ) as mocks:
            result = await router.route(request, "test-key")

        assert result == expected
        mocks["openai"].assert_awaited_once()
        mocks["gemini"].assert_not_awaited()
        mocks["anthropic"].assert_not_awaited()

    @pytest.mark.asyncio
    async def test_gemini_succeeds_no_fallback(self):
        """When the primary Gemini provider succeeds, no fallback is attempted."""
        router = ProviderRouter()
        request = _make_request("gemini-pro")
        expected = {"id": "gemini-1"}

        with _patch_providers(
            router,
            gemini=expected,
            openai={"id": "openai-1"},
            anthropic={"id": "anthropic-1"},
        ) as mocks:
            result = await router.route(request, "test-key")

        assert result == expected
        mocks["gemini"].assert_awaited_once()
        mocks["openai"].assert_not_awaited()
        mocks["anthropic"].assert_not_awaited()

    @pytest.mark.asyncio
    async def test_anthropic_succeeds_no_fallback(self):
        """When the primary Anthropic provider succeeds, no fallback is attempted."""
        router = ProviderRouter()
        request = _make_request("claude-3-5-sonnet")
        expected = {"id": "anthropic-1"}

        with _patch_providers(
            router,
            anthropic=expected,
            openai={"id": "openai-1"},
            gemini={"id": "gemini-1"},
        ) as mocks:
            result = await router.route(request, "test-key")

        assert result == expected
        mocks["anthropic"].assert_awaited_once()
        mocks["openai"].assert_not_awaited()
        mocks["gemini"].assert_not_awaited()


class TestTimeoutFallback:
    @pytest.mark.asyncio
    async def test_asyncio_timeout_falls_back(self):
        """asyncio.TimeoutError triggers a fallback to the next provider."""
        router = ProviderRouter()
        request = _make_request("gpt-4")

        with _patch_providers(
            router,
            openai=asyncio.TimeoutError(),
            gemini={"id": "gemini-1"},
            anthropic={"id": "anthropic-1"},
        ) as mocks:
            result = await router.route(request, "test-key")

        assert result == {"id": "gemini-1"}
        mocks["openai"].assert_awaited_once()
        mocks["gemini"].assert_awaited_once()
        mocks["anthropic"].assert_not_awaited()

    @pytest.mark.asyncio
    async def test_provider_timeout_falls_back(self):
        """ProviderTimeoutError triggers a fallback to the next provider."""
        router = ProviderRouter()
        request = _make_request("gpt-4")

        with _patch_providers(
            router,
            openai=ProviderTimeoutError("timed out"),
            gemini={"id": "gemini-1"},
            anthropic={"id": "anthropic-1"},
        ) as mocks:
            result = await router.route(request, "test-key")

        assert result == {"id": "gemini-1"}
        mocks["openai"].assert_awaited_once()
        mocks["gemini"].assert_awaited_once()
        mocks["anthropic"].assert_not_awaited()


class TestRateLimitFallback:
    @pytest.mark.asyncio
    async def test_rate_limit_falls_back(self):
        """ProviderRateLimitError triggers a fallback to the next provider."""
        router = ProviderRouter()
        request = _make_request("gpt-4")

        with _patch_providers(
            router,
            openai=ProviderRateLimitError("rate limited"),
            gemini={"id": "gemini-1"},
            anthropic={"id": "anthropic-1"},
        ) as mocks:
            result = await router.route(request, "test-key")

        assert result == {"id": "gemini-1"}
        mocks["openai"].assert_awaited_once()
        mocks["gemini"].assert_awaited_once()
        mocks["anthropic"].assert_not_awaited()


class TestAPIErrorFallback:
    @pytest.mark.asyncio
    async def test_api_error_falls_back(self):
        """ProviderAPIError triggers a fallback to the next provider."""
        router = ProviderRouter()
        request = _make_request("gpt-4")

        with _patch_providers(
            router,
            openai=ProviderAPIError("server error"),
            gemini={"id": "gemini-1"},
            anthropic={"id": "anthropic-1"},
        ) as mocks:
            result = await router.route(request, "test-key")

        assert result == {"id": "gemini-1"}
        mocks["openai"].assert_awaited_once()
        mocks["gemini"].assert_awaited_once()
        mocks["anthropic"].assert_not_awaited()


class TestNoFallback:
    @pytest.mark.asyncio
    async def test_authentication_error_no_fallback(self):
        """ProviderAuthenticationError returns immediately without fallback."""
        router = ProviderRouter()
        request = _make_request("gpt-4")

        with _patch_providers(
            router,
            openai=ProviderAuthenticationError("bad key"),
            gemini={"id": "gemini-1"},
            anthropic={"id": "anthropic-1"},
        ) as mocks:
            result = await router.route(request, "test-key")

        assert result["error"]["code"] == 401
        assert "authentication" in result["error"]["message"].lower()
        mocks["openai"].assert_awaited_once()
        mocks["gemini"].assert_not_awaited()
        mocks["anthropic"].assert_not_awaited()

    @pytest.mark.asyncio
    async def test_configuration_error_no_fallback(self):
        """ProviderConfigurationError returns immediately without fallback."""
        router = ProviderRouter()
        request = _make_request("gpt-4")

        with _patch_providers(
            router,
            openai=ProviderConfigurationError("misconfigured"),
            gemini={"id": "gemini-1"},
            anthropic={"id": "anthropic-1"},
        ) as mocks:
            result = await router.route(request, "test-key")

        assert result["error"]["code"] == 500
        assert "configuration" in result["error"]["message"].lower()
        mocks["openai"].assert_awaited_once()
        mocks["gemini"].assert_not_awaited()
        mocks["anthropic"].assert_not_awaited()


class TestAllProvidersFail:
    @pytest.mark.asyncio
    async def test_all_providers_fail_returns_error(self):
        """When every provider fails, an error response is returned."""
        router = ProviderRouter()
        request = _make_request("gpt-4")

        with _patch_providers(
            router,
            openai=ProviderTimeoutError("timeout"),
            gemini=ProviderRateLimitError("rate limited"),
            anthropic=ProviderAPIError("server error"),
        ) as mocks:
            result = await router.route(request, "test-key")

        assert result["error"]["code"] == 500
        assert "all providers failed" in result["error"]["message"].lower()
        mocks["openai"].assert_awaited_once()
        mocks["gemini"].assert_awaited_once()
        mocks["anthropic"].assert_awaited_once()

    @pytest.mark.asyncio
    async def test_all_providers_fail_with_rate_limit_last(self):
        """When the last provider fails with a rate limit, a 429 is returned."""
        router = ProviderRouter()
        request = _make_request("gpt-4")

        with _patch_providers(
            router,
            openai=ProviderTimeoutError("timeout"),
            gemini=ProviderTimeoutError("timeout"),
            anthropic=ProviderRateLimitError("rate limited"),
        ) as mocks:
            result = await router.route(request, "test-key")

        assert result["error"]["code"] == 429
        mocks["openai"].assert_awaited_once()
        mocks["gemini"].assert_awaited_once()
        mocks["anthropic"].assert_awaited_once()


class TestFallbackOrdering:
    @pytest.mark.asyncio
    async def test_openai_request_order(self):
        """OpenAI requests try OpenAI, then Gemini, then Anthropic."""
        router = ProviderRouter()
        request = _make_request("gpt-4")

        with _patch_providers(
            router,
            openai=ProviderTimeoutError("timeout"),
            gemini=ProviderTimeoutError("timeout"),
            anthropic={"id": "anthropic-1"},
        ) as mocks:
            result = await router.route(request, "test-key")

        assert result == {"id": "anthropic-1"}
        mocks["openai"].assert_awaited_once()
        mocks["gemini"].assert_awaited_once()
        mocks["anthropic"].assert_awaited_once()

    @pytest.mark.asyncio
    async def test_gemini_request_order(self):
        """Gemini requests try Gemini, then OpenAI, then Anthropic."""
        router = ProviderRouter()
        request = _make_request("gemini-pro")

        with _patch_providers(
            router,
            gemini=ProviderTimeoutError("timeout"),
            openai=ProviderTimeoutError("timeout"),
            anthropic={"id": "anthropic-1"},
        ) as mocks:
            result = await router.route(request, "test-key")

        assert result == {"id": "anthropic-1"}
        mocks["gemini"].assert_awaited_once()
        mocks["openai"].assert_awaited_once()
        mocks["anthropic"].assert_awaited_once()

    @pytest.mark.asyncio
    async def test_anthropic_request_order(self):
        """Anthropic requests try Anthropic, then OpenAI, then Gemini."""
        router = ProviderRouter()
        request = _make_request("claude-3-5-sonnet")

        with _patch_providers(
            router,
            anthropic=ProviderTimeoutError("timeout"),
            openai=ProviderTimeoutError("timeout"),
            gemini={"id": "gemini-1"},
        ) as mocks:
            result = await router.route(request, "test-key")

        assert result == {"id": "gemini-1"}
        mocks["anthropic"].assert_awaited_once()
        mocks["openai"].assert_awaited_once()
        mocks["gemini"].assert_awaited_once()

    @pytest.mark.asyncio
    async def test_fallback_order_is_centralized(self):
        """The fallback order is defined centrally on the router class."""
        assert ProviderRouter.FALLBACK_ORDER == {
            "openai": ["openai", "gemini", "anthropic"],
            "gemini": ["gemini", "openai", "anthropic"],
            "anthropic": ["anthropic", "openai", "gemini"],
        }


class TestLogging:
    @pytest.mark.asyncio
    async def test_fallback_logs_original_reason_new_and_attempt(self):
        """Each fallback logs the original provider, reason, new provider, and attempt."""
        router = ProviderRouter()
        request = _make_request("gpt-4")

        with _patch_providers(
            router,
            openai=ProviderTimeoutError("timed out"),
            gemini={"id": "gemini-1"},
            anthropic={"id": "anthropic-1"},
        ) as mocks, patch("providers.router.logger") as mock_logger:
            await router.route(request, "test-key")

        # The first fallback: OpenAI -> Gemini, attempt 1
        mock_logger.info.assert_any_call(
            "Provider %s failed (attempt %d): %s. Falling back to %s.",
            "openai",
            1,
            mocks["openai"].side_effect,
            "gemini",
        )

    @pytest.mark.asyncio
    async def test_all_providers_fail_logs_every_attempt(self):
        """When every provider fails, each attempt is logged."""
        router = ProviderRouter()
        request = _make_request("gpt-4")

        with _patch_providers(
            router,
            openai=ProviderTimeoutError("timeout"),
            gemini=ProviderRateLimitError("rate limited"),
            anthropic=ProviderAPIError("server error"),
        ) as mocks, patch("providers.router.logger") as mock_logger:
            await router.route(request, "test-key")

        # Attempt 1: OpenAI -> Gemini
        mock_logger.info.assert_any_call(
            "Provider %s failed (attempt %d): %s. Falling back to %s.",
            "openai",
            1,
            mocks["openai"].side_effect,
            "gemini",
        )
        # Attempt 2: Gemini -> Anthropic
        mock_logger.info.assert_any_call(
            "Provider %s failed (attempt %d): %s. Falling back to %s.",
            "openai",
            2,
            mocks["gemini"].side_effect,
            "anthropic",
        )
        # Attempt 3: Anthropic -> no more providers
        mock_logger.info.assert_any_call(
            "Provider %s failed (attempt %d): %s. No more providers to try.",
            "openai",
            3,
            mocks["anthropic"].side_effect,
        )


class TestProviderSwitching:
    @pytest.mark.asyncio
    async def test_switches_from_openai_to_gemini(self):
        """A failed OpenAI request is served by Gemini."""
        router = ProviderRouter()
        request = _make_request("gpt-4")

        with _patch_providers(
            router,
            openai=ProviderAPIError("server error"),
            gemini={"id": "gemini-1"},
            anthropic={"id": "anthropic-1"},
        ) as mocks:
            result = await router.route(request, "test-key")

        assert result == {"id": "gemini-1"}
        mocks["openai"].assert_awaited_once()
        mocks["gemini"].assert_awaited_once()
        mocks["anthropic"].assert_not_awaited()

    @pytest.mark.asyncio
    async def test_switches_from_gemini_to_openai(self):
        """A failed Gemini request is served by OpenAI."""
        router = ProviderRouter()
        request = _make_request("gemini-pro")

        with _patch_providers(
            router,
            gemini=ProviderAPIError("server error"),
            openai={"id": "openai-1"},
            anthropic={"id": "anthropic-1"},
        ) as mocks:
            result = await router.route(request, "test-key")

        assert result == {"id": "openai-1"}
        mocks["gemini"].assert_awaited_once()
        mocks["openai"].assert_awaited_once()
        mocks["anthropic"].assert_not_awaited()

    @pytest.mark.asyncio
    async def test_switches_from_anthropic_to_openai(self):
        """A failed Anthropic request is served by OpenAI."""
        router = ProviderRouter()
        request = _make_request("claude-3-5-sonnet")

        with _patch_providers(
            router,
            anthropic=ProviderAPIError("server error"),
            openai={"id": "openai-1"},
            gemini={"id": "gemini-1"},
        ) as mocks:
            result = await router.route(request, "test-key")

        assert result == {"id": "openai-1"}
        mocks["anthropic"].assert_awaited_once()
        mocks["openai"].assert_awaited_once()
        mocks["gemini"].assert_not_awaited()

    @pytest.mark.asyncio
    async def test_returns_first_successful_response(self):
        """The first successful response is returned; responses are never merged."""
        router = ProviderRouter()
        request = _make_request("gpt-4")

        with _patch_providers(
            router,
            openai=ProviderTimeoutError("timeout"),
            gemini={"id": "gemini-1", "choices": [{"message": {"content": "A"}}]},
            anthropic={"id": "anthropic-1", "choices": [{"message": {"content": "B"}}]},
        ) as mocks:
            result = await router.route(request, "test-key")

        # Only the Gemini response is returned, not a merge.
        assert result == {"id": "gemini-1", "choices": [{"message": {"content": "A"}}]}
        mocks["anthropic"].assert_not_awaited()


@pytest.fixture(autouse=True)
def _disable_retry_for_fallback_tests(monkeypatch):
    """Autouse, scoped to this module (Issue #21 fallback tests).

    Issue #22 adds per-provider retry-with-backoff *before* a provider is
    abandoned for fallback.  Setting max attempts to 1 here (one total attempt,
    no retries, no backoff sleeps) keeps these fallback tests fast and focused
    on the fallback behaviour they were written to verify.  Retry behaviour is
    covered separately by ``tests/test_provider_retry.py``.
    """
    monkeypatch.setenv("PROVIDER_RETRY_MAX_ATTEMPTS", "1")
