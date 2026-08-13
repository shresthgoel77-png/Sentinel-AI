"""Exponential-backoff retry for transient provider failures.

Issue #22 - retry provider requests after transient failures using a
configurable exponential backoff, without duplicating retry loops inside
every provider implementation.

Design summary
--------------
* Reusable async helper integrated at the lowest common provider-request layer
  (``ProviderRouter._try_provider``) so every provider benefits from it.
* Retry classification reuses the repository's existing provider exception
  hierarchy; no new exception types are introduced.
* Only transient/recoverable failures are retried.  Authentication,
  configuration and validation errors propagate immediately.
* Backoff uses ``asyncio.sleep`` (never ``time.sleep``) so the event loop is
  never blocked, and is capped by a configurable maximum.
* No sleep occurs after the final failed attempt and the original exception
  is re-raised (bare ``raise``) when retries are exhausted, leaving the
  existing circuit breaker and fallback behaviour untouched.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Awaitable, Callable

from exceptions.provider_exceptions import (
    ProviderAPIError,
    ProviderAuthenticationError,
    ProviderConfigurationError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    SentinelProviderError,
)

logger = logging.getLogger("sentinel.providers.retry")

# Failures considered transient/recoverable and therefore safe to retry.
# This intentionally mirrors the router's recoverable-exception set so retry
# classification and provider-fallback agree on what counts as transient.
#
# NOT included:
#   * ProviderAuthenticationError -> credentials/config wrong; retrying is
#                                  pointless and may worsen the situation.
#   * ProviderConfigurationError  -> misconfigured provider; retrying would
#                                  deterministically fail again.
#   * other SentinelProviderError -> unknown/application errors are treated as
#                                  non-transient to avoid retrying failures
#                                  that will not recover.
RETRYABLE_EXCEPTIONS: tuple = (
    ProviderTimeoutError,
    ProviderRateLimitError,
    ProviderAPIError,
    asyncio.TimeoutError,
)

# Auth/configuration failures: deterministic, never worth retrying.
_NON_RETRYABLE_EXCEPTIONS: tuple = (
    ProviderAuthenticationError,
    ProviderConfigurationError,
)


def is_retryable(exc: BaseException) -> bool:
    """Return ``True`` if ``exc`` is a transient, retryable failure.

    Uses the repository's existing exception hierarchy, so any future
    provider-specific transient exception that subclasses one of the above
    types is automatically retryable.
    """
    return isinstance(exc, RETRYABLE_EXCEPTIONS)


def is_non_retryable(exc: BaseException) -> bool:
    """Return ``True`` if ``exc`` is an auth/configuration failure.

    Such failures bypass retrying *and* circuit-breaking because they are
    deterministic and retrying them provides no benefit.
    """
    return isinstance(exc, _NON_RETRYABLE_EXCEPTIONS)


def exponential_backoff_delay(
    retry_number: int,
    initial_backoff: float,
    max_backoff: float,
) -> float:
    """Return the delay (seconds) to wait before a given retry.

    ``retry_number`` is 1-based: ``1`` is the first retry (after the initial
    attempt).  The delay grows exponentially::

        delay = initial_backoff * 2 ** (retry_number - 1)

    and is capped at ``max_backoff``.  Example with
    ``initial_backoff=1.0, max_backoff=8.0``:

    retry 1 -> 1.0s, retry 2 -> 2.0s, retry 3 -> 4.0s, retry 4 -> 8.0s, ...
    """
    if retry_number < 1:
        raise ValueError("retry_number must be >= 1")
    if initial_backoff < 0:
        raise ValueError("initial_backoff must be non-negative")
    if max_backoff < 0:
        raise ValueError("max_backoff must be non-negative")

    delay = initial_backoff * (2 ** (retry_number - 1))
    return float(min(delay, max_backoff))


async def retry_with_exponential_backoff(
    operation: Callable[[], Awaitable[Any]],
    *,
    provider_name: str,
    max_attempts: int = 3,
    initial_backoff: float = 1.0,
    max_backoff: float = 30.0,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
) -> Any:
    """Run ``operation`` with exponential-backoff retries on transient failures.

    Parameters
    ----------
    operation:
        An awaitable factory invoked for each attempt.  On success its return
        value is returned immediately and no further attempts are made.
    provider_name:
        Human-readable provider name used in structured log records.  Never
        logged with secrets.
    max_attempts:
        Total number of attempts (including the initial one).  Must be >= 1.
    initial_backoff:
        Delay before the first retry, in seconds.
    max_backoff:
        Upper bound for any single backoff delay, in seconds.
    sleep:
        Awaitable used to pause between attempts.  Defaults to
        :func:`asyncio.sleep`; injected for testing so delays never block.

    Behaviour
    ---------
    * Stops immediately after the first successful request.
    * Retries only transient/recoverable failures (timeout, rate limit, 5xx,
      connection errors).
    * Non-retryable failures (authentication, configuration, validation,
      other application errors) propagate immediately without retrying.
    * Waits ``initial_backoff * 2 ^ (attempt - 1)`` (capped at
      ``max_backoff``) between attempts using ``await sleep(...)``.
    * No sleep occurs after the final failed attempt.
    * When all attempts are exhausted the original, final exception is
      re-raised (bare ``raise``) preserving its traceback, type and cause.
    """
    if max_attempts < 1:
        raise ValueError("max_attempts must be >= 1")

    for attempt in range(1, max_attempts + 1):
        try:
            return await operation()
        except RETRYABLE_EXCEPTIONS as exc:
            # Final attempt: do not sleep or retry further.  Re-raise the
            # original exception (bare raise) to preserve the final, meaningful
            # exception for the caller and the circuit breaker.
            if attempt >= max_attempts:
                logger.error(
                    "Provider %s exhausted retries after %d attempt(s): "
                    "%s: %s",
                    provider_name,
                    attempt,
                    type(exc).__name__,
                    exc,
                )
                raise

            delay = exponential_backoff_delay(
                attempt, initial_backoff, max_backoff
            )
            # ``attempt`` is the 1-based number of the attempt that just
            # failed; the retry about to run is retry number ``attempt``.
            logger.warning(
                "Provider %s transient failure on attempt %d/%d: "
                "%s: %s. Retrying in %.2fs",
                provider_name,
                attempt,
                max_attempts,
                type(exc).__name__,
                exc,
                delay,
            )
            await sleep(delay)
            # Loop continues to the next attempt.

