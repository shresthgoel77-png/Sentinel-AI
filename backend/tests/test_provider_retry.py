# pyrefly: ignore [missing-import]
"""Unit tests for the exponential-backoff retry mechanism (Issue #22).

Covers the reusable retry helpers in ``providers.retry`` and their
integration with the provider router's existing fallback flow (Issue #21).

No real provider SDK calls or real backoff waits are made: retry delays are
injected with a fake async sleep (or set to zero), so the suite is fast and
deterministic and never blocks the event loop.
"""

import asyncio
import logging
import os
import sys
from contextlib import ExitStack, contextmanager

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from exceptions.provider_exceptions import (
    ProviderAPIError,
    ProviderAuthenticationError,
    ProviderCircuitOpenError,
    ProviderConfigurationError,
    ProviderRateLimitError,
    ProviderTimeoutError,
)
from providers.retry import (
    RETRYABLE_EXCEPTIONS,
    exponential_backoff_delay,
    is_non_retryable,
    is_retryable,
    retry_with_exponential_backoff,
)
from providers.router import ProviderRouter


def _make_request(model: str = "gpt-4") -> MagicMock:
    """Build a minimal request mock carrying a model attribute."""
    request = MagicMock()
    request.model = model
    return request


def _patch_providers(router: ProviderRouter, **side_effects):
    """Patch each provider's ``generate_completion`` with an AsyncMock.

    ``side_effects`` maps provider names to a return value, a single
    exception, or a list of values consumed sequentially across calls (an
    exception that is retried, then a success value).  Yields a dict of the
    patched mocks.
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


def _recorded_delays(sleep: AsyncMock):
    """Return each delay argument passed to an injected async sleep."""
    return [
        c.args[0] if c.args else c.kwargs.get("delay", None)
        for c in sleep.call_args_list
    ]

# ---------------------------------------------------------------------------
# Exponential backoff maths
# ---------------------------------------------------------------------------

class TestExponentialBackoffDelay:
    def test_initial_retry_uses_initial_backoff(self):
        assert exponential_backoff_delay(1, 1.0, 30.0) == 1.0

    def test_delay_doubles_per_retry(self):
        assert exponential_backoff_delay(2, 1.0, 30.0) == 2.0
        assert exponential_backoff_delay(3, 1.0, 30.0) == 4.0
        assert exponential_backoff_delay(4, 1.0, 30.0) == 8.0

    def test_delay_is_capped_at_max_backoff(self):
        # 1.0 * 2**9 = 512.0, capped to 30.0
        assert exponential_backoff_delay(10, 1.0, 30.0) == 30.0

    def test_zero_initial_backoff_always_returns_zero(self):
        assert exponential_backoff_delay(5, 0.0, 30.0) == 0.0

    def test_rejects_zero_retry_number(self):
        with pytest.raises(ValueError):
            exponential_backoff_delay(0, 1.0, 30.0)

    def test_rejects_negative_initial_backoff(self):
        with pytest.raises(ValueError):
            exponential_backoff_delay(1, -1.0, 30.0)


# ---------------------------------------------------------------------------
# Retry classification (transient vs. non-transient)
# ---------------------------------------------------------------------------

class TestRetryClassification:
    @pytest.mark.parametrize(
        "exc",
        [
            ProviderTimeoutError("timeout"),
            ProviderRateLimitError("rate limit"),
            ProviderAPIError("5xx"),
            asyncio.TimeoutError(),
        ],
    )
    def test_transient_exceptions_are_retryable(self, exc):
        assert is_retryable(exc) is True
        assert is_non_retryable(exc) is False

    @pytest.mark.parametrize(
        "exc",
        [
            ProviderAuthenticationError("bad key"),
            ProviderConfigurationError("missing model"),
        ],
    )
    def test_auth_and_config_errors_are_not_retryable(self, exc):
        assert is_retryable(exc) is False
        assert is_non_retryable(exc) is True

    def test_circuit_open_error_is_neither(self):
        exc = ProviderCircuitOpenError("open")
        assert is_retryable(exc) is False
        assert is_non_retryable(exc) is False

    def test_unrelated_exception_is_neither(self):
        exc = ValueError("nope")
        assert is_retryable(exc) is False
        assert is_non_retryable(exc) is False

    def test_retryable_exceptions_tuple_contents(self):
        assert ProviderTimeoutError in RETRYABLE_EXCEPTIONS
        assert ProviderRateLimitError in RETRYABLE_EXCEPTIONS
        assert ProviderAPIError in RETRYABLE_EXCEPTIONS
        assert asyncio.TimeoutError in RETRYABLE_EXCEPTIONS
        assert ProviderAuthenticationError not in RETRYABLE_EXCEPTIONS
        assert ProviderConfigurationError not in RETRYABLE_EXCEPTIONS


# ---------------------------------------------------------------------------
# retry_with_exponential_backoff (injected sleep -> fast & deterministic)
# ---------------------------------------------------------------------------

class TestRetryLoop:
    @pytest.mark.asyncio
    async def test_success_on_first_attempt_no_sleep(self):
        operation = AsyncMock(return_value={"ok": True})
        sleep = AsyncMock()
        result = await retry_with_exponential_backoff(
            operation,
            provider_name="openai",
            max_attempts=3,
            initial_backoff=1.0,
            max_backoff=30.0,
            sleep=sleep,
        )
        assert result == {"ok": True}
        assert operation.await_count == 1
        assert sleep.await_count == 0

    @pytest.mark.asyncio
    async def test_single_transient_failure_then_success(self):
        operation = AsyncMock(
            side_effect=[ProviderTimeoutError("slow"), {"ok": True}]
        )
        sleep = AsyncMock()
        result = await retry_with_exponential_backoff(
            operation,
            provider_name="openai",
            max_attempts=3,
            initial_backoff=1.0,
            max_backoff=30.0,
            sleep=sleep,
        )
        assert result == {"ok": True}
        assert operation.await_count == 2
        assert sleep.await_count == 1
        assert _recorded_delays(sleep) == [1.0]

    @pytest.mark.asyncio
    async def test_multiple_transient_failures_then_success(self):
        operation = AsyncMock(
            side_effect=[
                ProviderAPIError("first"),
                ProviderRateLimitError("second"),
                {"ok": True},
            ]
        )
        sleep = AsyncMock()
        result = await retry_with_exponential_backoff(
            operation,
            provider_name="gemini",
            max_attempts=5,
            initial_backoff=1.0,
            max_backoff=30.0,
            sleep=sleep,
        )
        assert result == {"ok": True}
        assert operation.await_count == 3
        assert _recorded_delays(sleep) == [1.0, 2.0]

    @pytest.mark.asyncio
    async def test_stops_after_max_attempts_and_reraises(self):
        exc = ProviderAPIError("server down")
        operation = AsyncMock(side_effect=exc)
        sleep = AsyncMock()
        with pytest.raises(ProviderAPIError):
            await retry_with_exponential_backoff(
                operation,
                provider_name="openai",
                max_attempts=3,
                initial_backoff=1.0,
                max_backoff=30.0,
                sleep=sleep,
            )
        assert operation.await_count == 3
        # Two retries produce two sleeps; no sleep after the final attempt.
        assert sleep.await_count == 2
        assert _recorded_delays(sleep) == [1.0, 2.0]

    @pytest.mark.asyncio
    async def test_backoff_is_capped_by_max_backoff(self):
        operation = AsyncMock(side_effect=ProviderRateLimitError("rl"))
        sleep = AsyncMock()
        with pytest.raises(ProviderRateLimitError):
            await retry_with_exponential_backoff(
                operation,
                provider_name="openai",
                max_attempts=4,
                initial_backoff=10.0,
                max_backoff=15.0,
                sleep=sleep,
            )
        # Delays are 10.0, then 20.0 and 40.0 (both capped to 15.0);
        # no sleep occurs after the 4th and final attempt.
        assert _recorded_delays(sleep) == [10.0, 15.0, 15.0]
        assert operation.await_count == 4

    @pytest.mark.asyncio
    async def test_rate_limit_error_is_retried(self):
        operation = AsyncMock(
            side_effect=[ProviderRateLimitError("429"), {"ok": True}]
        )
        sleep = AsyncMock()
        result = await retry_with_exponential_backoff(
            operation,
            provider_name="anthropic",
            max_attempts=3,
            initial_backoff=0.5,
            max_backoff=30.0,
            sleep=sleep,
        )
        assert result == {"ok": True}
        assert operation.await_count == 2
        assert _recorded_delays(sleep) == [0.5]

    @pytest.mark.asyncio
    async def test_timeout_error_is_retried(self):
        operation = AsyncMock(
            side_effect=[asyncio.TimeoutError(), {"ok": True}]
        )
        sleep = AsyncMock()
        result = await retry_with_exponential_backoff(
            operation,
            provider_name="openai",
            max_attempts=3,
            initial_backoff=1.0,
            max_backoff=30.0,
            sleep=sleep,
        )
        assert result == {"ok": True}
        assert operation.await_count == 2
        assert sleep.await_count == 1

    @pytest.mark.asyncio
    async def test_auth_error_is_not_retried(self):
        operation = AsyncMock(side_effect=ProviderAuthenticationError("denied"))
        sleep = AsyncMock()
        with pytest.raises(ProviderAuthenticationError):
            await retry_with_exponential_backoff(
                operation,
                provider_name="openai",
                max_attempts=3,
                initial_backoff=1.0,
                max_backoff=30.0,
                sleep=sleep,
            )
        assert operation.await_count == 1
        assert sleep.await_count == 0

    @pytest.mark.asyncio
    async def test_config_error_is_not_retried(self):
        operation = AsyncMock(side_effect=ProviderConfigurationError("misconfig"))
        sleep = AsyncMock()
        with pytest.raises(ProviderConfigurationError):
            await retry_with_exponential_backoff(
                operation,
                provider_name="gemini",
                max_attempts=3,
                initial_backoff=1.0,
                max_backoff=30.0,
                sleep=sleep,
            )
        assert operation.await_count == 1
        assert sleep.await_count == 0

    @pytest.mark.asyncio
    async def test_final_exception_instance_is_preserved(self):
        original = ProviderAPIError("boom")
        operation = AsyncMock(side_effect=original)
        sleep = AsyncMock()
        with pytest.raises(ProviderAPIError) as exc_info:
            await retry_with_exponential_backoff(
                operation,
                provider_name="openai",
                max_attempts=2,
                initial_backoff=1.0,
                max_backoff=30.0,
                sleep=sleep,
            )
        assert exc_info.value is original

    @pytest.mark.asyncio
    async def test_max_attempts_of_one_does_not_retry(self):
        operation = AsyncMock(side_effect=ProviderTimeoutError("t"))
        sleep = AsyncMock()
        with pytest.raises(ProviderTimeoutError):
            await retry_with_exponential_backoff(
                operation,
                provider_name="openai",
                max_attempts=1,
                initial_backoff=1.0,
                max_backoff=30.0,
                sleep=sleep,
            )
        assert operation.await_count == 1
        assert sleep.await_count == 0

    @pytest.mark.asyncio
    async def test_waits_using_awaitable_sleep_not_blocking(self):
        # A failing then succeeding operation must pause via the injected
        # awaitable (never time.sleep), keeping the event loop unblocked.
        operation = AsyncMock(
            side_effect=[ProviderTimeoutError("t"), {"ok": True}]
        )
        sleep = AsyncMock()
        await retry_with_exponential_backoff(
            operation,
            provider_name="openai",
            max_attempts=3,
            initial_backoff=1.0,
            max_backoff=30.0,
            sleep=sleep,
        )
        sleep.assert_awaited_once()
        assert operation.await_count == 2

    @pytest.mark.asyncio
    async def test_rejects_max_attempts_below_one(self):
        with pytest.raises(ValueError):
            await retry_with_exponential_backoff(
                AsyncMock(), provider_name="openai", max_attempts=0
            )


# ---------------------------------------------------------------------------
# Router integration: retry the same provider before falling back (Issue #21)
# ---------------------------------------------------------------------------

class TestRouterRetryIntegration:
    """End-to-end retry-then-fallback via ``ProviderRouter.route``.

    ``retry_initial_backoff`` and ``retry_max_backoff`` are set to ``0.0`` so
    ``asyncio.sleep(0.0)`` yields instantly and the suite never waits on the
    configured backoff delays.
    """

    @pytest.mark.asyncio
    async def test_retries_same_provider_before_fallback(self):
        router = ProviderRouter()
        router.retry_max_attempts = 3
        router.retry_initial_backoff = 0.0
        router.retry_max_backoff = 0.0
        request = _make_request("gpt-4")
        success = {"id": "openai-1"}
        with _patch_providers(
            router,
            openai=[ProviderTimeoutError("slow"), success],
            gemini={"id": "gemini-1"},
            anthropic={"id": "anthropic-1"},
        ) as mocks:
            result = await router.route(request, "test-key")

        assert result == success
        # The transient failure was handled by retrying OpenAI itself.
        assert mocks["openai"].await_count == 2
        assert mocks["gemini"].await_count == 0
        assert mocks["anthropic"].await_count == 0

    @pytest.mark.asyncio
    async def test_fallback_only_after_retries_exhausted(self):
        router = ProviderRouter()
        router.retry_max_attempts = 3
        router.retry_initial_backoff = 0.0
        router.retry_max_backoff = 0.0
        request = _make_request("gpt-4")
        with _patch_providers(
            router,
            openai=ProviderAPIError("permanently down"),
            gemini={"id": "gemini-1"},
            anthropic={"id": "anthropic-1"},
        ) as mocks:
            result = await router.route(request, "test-key")

        assert result == {"id": "gemini-1"}
        # 3 attempts on OpenAI (2 retries) precede the existing fallback.
        assert mocks["openai"].await_count == 3
        assert mocks["gemini"].await_count == 1
        assert mocks["anthropic"].await_count == 0

    @pytest.mark.asyncio
    async def test_auth_error_skips_retry_and_fallback(self):
        router = ProviderRouter()
        router.retry_max_attempts = 3
        request = _make_request("gpt-4")
        with _patch_providers(
            router,
            openai=ProviderAuthenticationError("invalid key"),
            gemini={"id": "gemini-1"},
            anthropic={"id": "anthropic-1"},
        ) as mocks:
            result = await router.route(request, "test-key")

        assert result["error"]["code"] == 401
        assert mocks["openai"].await_count == 1
        assert mocks["gemini"].await_count == 0
        assert mocks["anthropic"].await_count == 0


# ---------------------------------------------------------------------------
# Retry logging
# ---------------------------------------------------------------------------

class TestRetryLogging:
    @pytest.mark.asyncio
    async def test_retry_attempts_are_logged_with_context(self, caplog):
        operation = AsyncMock(
            side_effect=[ProviderRateLimitError("429"), {"ok": True}]
        )
        sleep = AsyncMock()

        with caplog.at_level(logging.WARNING, logger="sentinel.providers.retry"):
            await retry_with_exponential_backoff(
                operation,
                provider_name="openai",
                max_attempts=3,
                initial_backoff=1.0,
                max_backoff=30.0,
                sleep=sleep,
            )

        warning = next(
            (r for r in caplog.records if r.levelno == logging.WARNING), None
        )
        assert warning is not None
        message = warning.getMessage()
        assert "openai" in message
        assert "1/3" in message  # current attempt / max attempts
        assert "ProviderRateLimitError" in message


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

class TestRetryConfiguration:
    def test_router_uses_sensible_retry_defaults(self):
        router = ProviderRouter()
        assert router.retry_max_attempts == 3
        assert router.retry_initial_backoff == 1.0
        assert router.retry_max_backoff == 30.0

    def test_router_reads_retry_config_from_environment(self, monkeypatch):
        monkeypatch.setenv("PROVIDER_RETRY_MAX_ATTEMPTS", "5")
        monkeypatch.setenv("PROVIDER_RETRY_INITIAL_BACKOFF", "0.25")
        monkeypatch.setenv("PROVIDER_RETRY_MAX_BACKOFF", "8.0")
        router = ProviderRouter()
        assert router.retry_max_attempts == 5
        assert router.retry_initial_backoff == 0.25
        assert router.retry_max_backoff == 8.0
