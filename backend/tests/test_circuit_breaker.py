# pyrefly: ignore [missing-import]
"""Unit tests for the provider circuit breaker (Issue #23).

Covers state transitions, provider isolation, concurrency, failure
classification, reset behavior, and configurable timing.
"""

import asyncio
import sys
import os

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from providers.circuit_breaker import (
    CircuitBreakerState,
    ProviderCircuitBreaker,
)
from providers.router import ProviderRouter
from exceptions.provider_exceptions import (
    ProviderAPIError,
    ProviderAuthenticationError,
    ProviderTimeoutError,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_request(model: str = "gpt-4") -> MagicMock:
    request = MagicMock()
    request.model = model
    return request


# ---------------------------------------------------------------------------
# CircuitBreakerState tests
# ---------------------------------------------------------------------------

class TestCircuitBreakerState:
    def test_state_values(self):
        assert CircuitBreakerState.CLOSED == "CLOSED"
        assert CircuitBreakerState.OPEN == "OPEN"
        assert CircuitBreakerState.HALF_OPEN == "HALF_OPEN"


# ---------------------------------------------------------------------------
# ProviderCircuitBreaker core tests
# ---------------------------------------------------------------------------

class TestProviderCircuitBreaker:
    def test_initial_state_is_closed(self):
        cb = ProviderCircuitBreaker(failure_threshold=2, recovery_timeout=1.0)
        assert cb.get_state("openai") == CircuitBreakerState.CLOSED
        assert cb.get_failure_count("openai") == 0

    @pytest.mark.asyncio
    async def test_success_resets_failure_count(self):
        cb = ProviderCircuitBreaker(failure_threshold=3, recovery_timeout=1.0)
        await cb.record_failure("openai")
        await cb.record_failure("openai")
        assert cb.get_failure_count("openai") == 2
        await cb.record_success("openai")
        assert cb.get_failure_count("openai") == 0
        assert cb.get_state("openai") == CircuitBreakerState.CLOSED

    @pytest.mark.asyncio
    async def test_threshold_opens_circuit(self):
        cb = ProviderCircuitBreaker(failure_threshold=3, recovery_timeout=1.0)
        for _ in range(3):
            await cb.record_failure("openai")
        assert cb.get_state("openai") == CircuitBreakerState.OPEN
        assert cb.get_failure_count("openai") == 3

    @pytest.mark.asyncio
    async def test_open_circuit_rejects_requests(self):
        cb = ProviderCircuitBreaker(failure_threshold=2, recovery_timeout=1.0)
        await cb.record_failure("openai")
        await cb.record_failure("openai")
        assert cb.get_state("openai") == CircuitBreakerState.OPEN
        assert await cb.allow_request("openai") is False

    @pytest.mark.asyncio
    async def test_recovery_timeout_transitions_to_half_open(self):
        cb = ProviderCircuitBreaker(failure_threshold=2, recovery_timeout=0.1)
        await cb.record_failure("openai")
        await cb.record_failure("openai")
        assert cb.get_state("openai") == CircuitBreakerState.OPEN

        await asyncio.sleep(0.15)
        assert await cb.allow_request("openai") is True
        assert cb.get_state("openai") == CircuitBreakerState.HALF_OPEN

    @pytest.mark.asyncio
    async def test_half_open_success_closes_circuit(self):
        cb = ProviderCircuitBreaker(failure_threshold=2, recovery_timeout=0.05)
        await cb.record_failure("openai")
        await cb.record_failure("openai")
        await asyncio.sleep(0.1)
        assert await cb.allow_request("openai") is True
        await cb.record_success("openai")
        assert cb.get_state("openai") == CircuitBreakerState.CLOSED
        assert cb.get_failure_count("openai") == 0

    @pytest.mark.asyncio
    async def test_half_open_failure_reopens_circuit(self):
        cb = ProviderCircuitBreaker(failure_threshold=2, recovery_timeout=0.05)
        await cb.record_failure("openai")
        await cb.record_failure("openai")
        await asyncio.sleep(0.1)
        assert await cb.allow_request("openai") is True
        await cb.record_failure("openai")
        assert cb.get_state("openai") == CircuitBreakerState.OPEN

    @pytest.mark.asyncio
    async def test_half_open_only_one_probe_in_progress(self):
        cb = ProviderCircuitBreaker(failure_threshold=2, recovery_timeout=0.05)
        await cb.record_failure("openai")
        await cb.record_failure("openai")
        await asyncio.sleep(0.1)

        results = await asyncio.gather(
            cb.allow_request("openai"),
            cb.allow_request("openai"),
            cb.allow_request("openai"),
        )
        assert results == [True, False, False]

    @pytest.mark.asyncio
    async def test_manual_reset(self):
        cb = ProviderCircuitBreaker(failure_threshold=2, recovery_timeout=1.0)
        await cb.record_failure("openai")
        await cb.record_failure("openai")
        assert cb.get_state("openai") == CircuitBreakerState.OPEN
        await cb.reset("openai")
        assert cb.get_state("openai") == CircuitBreakerState.CLOSED
        assert cb.get_failure_count("openai") == 0
        assert await cb.allow_request("openai") is True

    @pytest.mark.asyncio
    async def test_provider_isolation(self):
        cb = ProviderCircuitBreaker(failure_threshold=2, recovery_timeout=1.0)
        await cb.record_failure("openai")
        await cb.record_failure("openai")
        assert cb.get_state("openai") == CircuitBreakerState.OPEN
        assert cb.get_state("gemini") == CircuitBreakerState.CLOSED
        assert await cb.allow_request("gemini") is True
        assert await cb.allow_request("openai") is False


# ---------------------------------------------------------------------------
# Router integration tests
# ---------------------------------------------------------------------------

class TestRouterCircuitBreakerIntegration:
    @pytest.mark.asyncio
    async def test_open_circuit_triggers_fallback(self):
        router = ProviderRouter()
        request = _make_request("gpt-4")

        # Force the circuit open for OpenAI.
        for _ in range(5):
            await router.circuit_breaker.record_failure("openai")
        assert router.circuit_breaker.get_state("openai") == CircuitBreakerState.OPEN

        with patch.object(
            router.providers["openai"], "generate_completion", new_callable=AsyncMock
        ) as mock_openai, patch.object(
            router.providers["gemini"], "generate_completion", new_callable=AsyncMock
        ) as mock_gemini:
            mock_gemini.return_value = {"id": "gemini-1"}
            result = await router.route(request, "test-key")

        assert result == {"id": "gemini-1"}
        mock_openai.assert_not_awaited()
        mock_gemini.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_successful_request_does_not_trip_circuit(self):
        router = ProviderRouter()
        request = _make_request("gpt-4")

        with patch.object(
            router.providers["openai"], "generate_completion", new_callable=AsyncMock
        ) as mock_openai:
            mock_openai.return_value = {"id": "openai-1"}
            result = await router.route(request, "test-key")

        assert result == {"id": "openai-1"}
        assert router.circuit_breaker.get_state("openai") == CircuitBreakerState.CLOSED

    @pytest.mark.asyncio
    async def test_recoverable_failure_increments_circuit_count(self):
        router = ProviderRouter()
        request = _make_request("gpt-4")

        with patch.object(
            router.providers["openai"], "generate_completion", new_callable=AsyncMock
        ) as mock_openai, patch.object(
            router.providers["gemini"], "generate_completion", new_callable=AsyncMock
        ) as mock_gemini:
            mock_openai.side_effect = ProviderTimeoutError("timeout")
            mock_gemini.return_value = {"id": "gemini-1"}
            result = await router.route(request, "test-key")

        assert result == {"id": "gemini-1"}
        assert router.circuit_breaker.get_failure_count("openai") == 1

    @pytest.mark.asyncio
    async def test_authentication_error_does_not_trip_circuit(self):
        router = ProviderRouter()
        request = _make_request("gpt-4")

        with patch.object(
            router.providers["openai"], "generate_completion", new_callable=AsyncMock
        ) as mock_openai:
            mock_openai.side_effect = ProviderAuthenticationError("bad key")
            result = await router.route(request, "test-key")

        assert result["error"]["code"] == 401
        assert router.circuit_breaker.get_failure_count("openai") == 0

    @pytest.mark.asyncio
    async def test_configurable_failure_threshold(self):
        """Circuit should open after the configured number of failures."""
        router = ProviderRouter()
        router.circuit_breaker = ProviderCircuitBreaker(
            failure_threshold=3, recovery_timeout=1.0
        )
        request = _make_request("gpt-4")

        with patch.object(
            router.providers["openai"], "generate_completion", new_callable=AsyncMock
        ) as mock_openai, patch.object(
            router.providers["gemini"], "generate_completion", new_callable=AsyncMock
        ) as mock_gemini:
            mock_openai.side_effect = ProviderAPIError("server error")
            mock_gemini.return_value = {"id": "gemini-1"}

            # Two failures should NOT open the circuit.
            await router.route(request, "test-key")
            await router.route(request, "test-key")
            assert router.circuit_breaker.get_state("openai") == CircuitBreakerState.CLOSED

            # Third failure should open it.
            await router.route(request, "test-key")
            assert router.circuit_breaker.get_state("openai") == CircuitBreakerState.OPEN


# ---------------------------------------------------------------------------
# Concurrency tests
# ---------------------------------------------------------------------------

class TestConcurrency:
    @pytest.mark.asyncio
    async def test_only_one_half_open_probe(self):
        cb = ProviderCircuitBreaker(failure_threshold=2, recovery_timeout=0.05)
        await cb.record_failure("openai")
        await cb.record_failure("openai")
        await asyncio.sleep(0.1)

        probe_attempts = []

        async def attempt():
            allowed = await cb.allow_request("openai")
            if allowed:
                probe_attempts.append(1)

        await asyncio.gather(*[attempt() for _ in range(20)])
        assert sum(probe_attempts) == 1


@pytest.fixture(autouse=True)
def _disable_retry_for_circuit_breaker_tests(monkeypatch):
    """Autouse, scoped to this module (Issue #22 compatibility).

    Issue #22 adds per-provider retry-with-backoff inside the router.  The
    circuit-breaker router tests exercise fallback/circuit behaviour and are
    written against single attempted providers; disabling retry here keeps them
    fast (no real backoff sleeps) and focused.  Retry behaviour is covered by
    ``tests/test_provider_retry.py``.
    """
    monkeypatch.setenv("PROVIDER_RETRY_MAX_ATTEMPTS", "1")
