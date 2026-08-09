"""Circuit breaker implementation for LLM provider health tracking.

Tracks consecutive provider failures and opens the circuit after a configurable
threshold. While open, providers are skipped to reduce cascading failures and
unnecessary latency. A half-open state periodically tests provider recovery.
"""

import asyncio
import logging
import time
from enum import Enum
from typing import Dict, Optional

logger = logging.getLogger("sentinel.providers.circuit_breaker")


class CircuitBreakerState(str, Enum):
    """Possible states for a provider circuit."""

    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class ProviderCircuitOpenError(Exception):
    """Raised when a request is rejected because the provider circuit is open."""


class ProviderCircuitBreaker:
    """Per-provider circuit breaker with configurable thresholds.

    State transitions:
        CLOSED -> OPEN   : consecutive failures >= threshold
        OPEN    -> HALF_OPEN : recovery timeout elapsed
        HALF_OPEN -> CLOSED : successful probe
        HALF_OPEN -> OPEN   : failed probe
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
    ) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout

        # Per-provider state
        self._states: Dict[str, CircuitBreakerState] = {}
        self._failure_counts: Dict[str, int] = {}
        self._opened_at: Dict[str, float] = {}
        self._half_open_in_progress: Dict[str, bool] = {}
        self._locks: Dict[str, asyncio.Lock] = {}

    def _get_lock(self, provider_name: str) -> asyncio.Lock:
        if provider_name not in self._locks:
            self._locks[provider_name] = asyncio.Lock()
        return self._locks[provider_name]

    def _ensure_state(self, provider_name: str) -> None:
        if provider_name not in self._states:
            self._states[provider_name] = CircuitBreakerState.CLOSED
            self._failure_counts[provider_name] = 0
            self._half_open_in_progress[provider_name] = False

    async def allow_request(self, provider_name: str) -> bool:
        """Check whether a request may proceed to the provider."""
        self._ensure_state(provider_name)
        state = self._states[provider_name]

        if state == CircuitBreakerState.CLOSED:
            return True

        if state == CircuitBreakerState.OPEN:
            opened_at = self._opened_at.get(provider_name, 0)
            if time.monotonic() - opened_at >= self.recovery_timeout:
                async with self._get_lock(provider_name):
                    if self._states[provider_name] == CircuitBreakerState.OPEN:
                        if time.monotonic() - self._opened_at.get(provider_name, 0) >= self.recovery_timeout:
                            self._states[provider_name] = CircuitBreakerState.HALF_OPEN
                            # The coroutine that transitions to HALF_OPEN becomes the probe.
                            self._half_open_in_progress[provider_name] = True
                            logger.info(
                                "Provider %s circuit transitioned to HALF_OPEN "
                                "after recovery timeout elapsed",
                                provider_name,
                            )
                            return True
                    return False
            return False

        if state == CircuitBreakerState.HALF_OPEN:
            async with self._get_lock(provider_name):
                if not self._half_open_in_progress.get(provider_name, False):
                    self._half_open_in_progress[provider_name] = True
                    logger.info(
                        "Provider %s recovery probe permitted (HALF_OPEN)",
                        provider_name,
                    )
                    return True
                logger.debug(
                    "Provider %s recovery probe already in progress, "
                    "skipping request",
                    provider_name,
                )
                return False

        return False

    async def record_success(self, provider_name: str) -> None:
        """Record a successful request for the provider."""
        self._ensure_state(provider_name)
        async with self._get_lock(provider_name):
            state = self._states[provider_name]
            if state == CircuitBreakerState.HALF_OPEN:
                self._states[provider_name] = CircuitBreakerState.CLOSED
                self._failure_counts[provider_name] = 0
                self._half_open_in_progress[provider_name] = False
                logger.info(
                    "Provider %s circuit closed after successful recovery probe",
                    provider_name,
                )
            elif state == CircuitBreakerState.CLOSED:
                self._failure_counts[provider_name] = 0

    async def record_failure(self, provider_name: str) -> None:
        """Record a failed request for the provider."""
        self._ensure_state(provider_name)
        async with self._get_lock(provider_name):
            state = self._states[provider_name]

            if state == CircuitBreakerState.HALF_OPEN:
                self._states[provider_name] = CircuitBreakerState.OPEN
                self._opened_at[provider_name] = time.monotonic()
                self._half_open_in_progress[provider_name] = False
                logger.warning(
                    "Provider %s recovery probe failed, circuit re-opened",
                    provider_name,
                )
                return

            if state == CircuitBreakerState.CLOSED:
                self._failure_counts[provider_name] = (
                    self._failure_counts.get(provider_name, 0) + 1
                )
                count = self._failure_counts[provider_name]
                logger.warning(
                    "Provider %s failure %d/%d",
                    provider_name,
                    count,
                    self.failure_threshold,
                )
                if count >= self.failure_threshold:
                    self._states[provider_name] = CircuitBreakerState.OPEN
                    self._opened_at[provider_name] = time.monotonic()
                    logger.error(
                        "Provider %s circuit opened after %d consecutive failures",
                        provider_name,
                        count,
                    )

    async def reset(self, provider_name: str) -> None:
        """Manually reset the circuit for a provider to CLOSED."""
        self._ensure_state(provider_name)
        async with self._get_lock(provider_name):
            self._states[provider_name] = CircuitBreakerState.CLOSED
            self._failure_counts[provider_name] = 0
            self._opened_at.pop(provider_name, None)
            self._half_open_in_progress[provider_name] = False
            logger.info("Provider %s circuit manually reset to CLOSED", provider_name)

    def get_state(self, provider_name: str) -> CircuitBreakerState:
        """Return the current circuit state for a provider."""
        self._ensure_state(provider_name)
        return self._states[provider_name]

    def get_failure_count(self, provider_name: str) -> int:
        """Return the current consecutive failure count for a provider."""
        self._ensure_state(provider_name)
        return self._failure_counts.get(provider_name, 0)

    def get_opened_at(self, provider_name: str) -> Optional[float]:
        """Return the timestamp when the circuit was opened, or None."""
        self._ensure_state(provider_name)
        return self._opened_at.get(provider_name)
