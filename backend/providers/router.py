import asyncio
import logging
import os
from typing import Any, Dict, List, Optional

from exceptions.provider_exceptions import (
    ProviderAuthenticationError,
    ProviderCircuitOpenError,
    ProviderConfigurationError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    SentinelProviderError,
)
from .anthropic import AnthropicProvider
from .circuit_breaker import ProviderCircuitBreaker
from .gemini import GeminiProvider
from .openai import OpenAIProvider
from .retry import RETRYABLE_EXCEPTIONS, retry_with_exponential_backoff

logger = logging.getLogger("sentinel.providers.router")

# Time budget applied to every individual provider attempt.
REQUEST_TIMEOUT_SECONDS = 30.0

# Exceptions that are considered recoverable and therefore trigger a fallback.
# Authentication and configuration failures are intentionally excluded.
_RECOVERABLE_EXCEPTIONS = RETRYABLE_EXCEPTIONS


class ProviderRouter:
    """Routes chat-completion requests to an LLM provider with automatic failover.

    The user-selected provider is always attempted first.  If it fails with a
    recoverable error (timeout, rate limit, temporary API failure, connection
    failure, or HTTP 5xx), the router transparently retries the next configured
    provider in a centralized, deterministic order.  The first successful
    response is returned immediately; responses are never merged.

    Non-recoverable failures (authentication, configuration, invalid request)
    are returned to the caller immediately without attempting a fallback.
    """

    # Centralized fallback ordering.  Each provider maps to the ordered list of
    # providers to try after it, preserving the user-selected provider first.
    FALLBACK_ORDER: Dict[str, List[str]] = {
        "openai": ["openai", "gemini", "anthropic"],
        "gemini": ["gemini", "openai", "anthropic"],
        "anthropic": ["anthropic", "openai", "gemini"],
    }

    def __init__(self):
        self.providers = {
            "openai": OpenAIProvider(),
            "anthropic": AnthropicProvider(),
            "gemini": GeminiProvider(),
        }
        self.circuit_breaker = ProviderCircuitBreaker(
            failure_threshold=int(
                os.getenv("CIRCUIT_BREAKER_FAILURE_THRESHOLD", "5")
            ),
            recovery_timeout=float(
                os.getenv("CIRCUIT_BREAKER_RECOVERY_TIMEOUT", "60.0")
            ),
        )

        # Retry configuration (Issue #22): exponential backoff between
        # attempts, applied before any provider fallback.
        self.retry_max_attempts = int(
            os.getenv("PROVIDER_RETRY_MAX_ATTEMPTS", "3")
        )
        self.retry_initial_backoff = float(
            os.getenv("PROVIDER_RETRY_INITIAL_BACKOFF", "1.0")
        )
        self.retry_max_backoff = float(
            os.getenv("PROVIDER_RETRY_MAX_BACKOFF", "30.0")
        )

    async def route(self, request, api_key: str) -> Dict[str, Any]:
        provider_name = self._get_provider_name(request.model)
        ordered_providers = self._fallback_order(provider_name)

        last_error: Optional[BaseException] = None
        for index, candidate in enumerate(ordered_providers):
            provider = self.providers[candidate]

            # Circuit breaker: skip providers with open circuits.
            if not await self.circuit_breaker.allow_request(candidate):
                logger.info(
                    "Provider %s request skipped because circuit is open",
                    candidate,
                )
                next_provider = self._next_provider(ordered_providers, index)
                self._log_fallback(
                    original_provider=provider_name,
                    reason=ProviderCircuitOpenError(
                        f"Provider {candidate} circuit is open"
                    ),
                    new_provider=next_provider,
                    attempt=index + 1,
                )
                continue

            try:
                result = await self._try_provider(
                    candidate,
                    provider,
                    request,
                    api_key,
                )
                await self.circuit_breaker.record_success(candidate)
                return result
            except _RECOVERABLE_EXCEPTIONS as exc:
                last_error = exc
                await self.circuit_breaker.record_failure(candidate)
                next_provider = self._next_provider(ordered_providers, index)
                self._log_fallback(
                    original_provider=provider_name,
                    reason=exc,
                    new_provider=next_provider,
                    attempt=index + 1,
                )
                continue
            except ProviderAuthenticationError as exc:
                # Non-recoverable: do not fall back, surface immediately.
                logger.warning(
                    "Provider %s authentication failed: %s",
                    candidate,
                    exc,
                )
                return self._error_response("Provider authentication failed", 401)
            except ProviderConfigurationError as exc:
                # Non-recoverable: do not fall back, surface immediately.
                logger.error(
                    "Provider %s configuration error: %s",
                    candidate,
                    exc,
                )
                return self._error_response("Provider configuration error", 500)
            except SentinelProviderError as exc:
                # Any other provider error is treated as non-recoverable.
                logger.error("Provider %s failed: %s", candidate, exc)
                return self._error_response("Provider error occurred", 500)

        # Every provider failed with a recoverable error.
        logger.error(
            "All providers failed for request. Last error: %s",
            last_error,
        )
        return self._error_response(
            "All providers failed", self._error_code(last_error)
        )

    async def _try_provider(
        self,
        provider_name: str,
        provider,
        request,
        api_key: str,
    ) -> Dict[str, Any]:
        """Invoke a single provider with the shared timeout and retry behavior.

        The provider call is wrapped in an ``asyncio.wait_for`` timeout and
        retried with exponential backoff on transient failures (timeout, rate
        limit, HTTP 5xx).  Non-retryable failures (authentication,
        configuration, other application errors) propagate immediately.  When
        retries are exhausted the final exception is re-raised so the caller
        (fallback loop / circuit breaker) can react.
        """

        async def _attempt() -> Dict[str, Any]:
            return await asyncio.wait_for(
                provider.generate_completion(request, api_key),
                timeout=REQUEST_TIMEOUT_SECONDS,
            )

        return await retry_with_exponential_backoff(
            _attempt,
            provider_name=provider_name,
            max_attempts=self.retry_max_attempts,
            initial_backoff=self.retry_initial_backoff,
            max_backoff=self.retry_max_backoff,
        )

    def _fallback_order(self, provider_name: str) -> List[str]:
        """Return the ordered list of providers to attempt for a request.

        The user-selected provider is always first.  Unknown provider names
        fall back to the default ordering.
        """
        return self.FALLBACK_ORDER.get(provider_name, self.FALLBACK_ORDER["gemini"])

    def _next_provider(self, ordered_providers: List[str], index: int) -> Optional[str]:
        """Return the provider to try next, or ``None`` if none remain."""
        if index + 1 < len(ordered_providers):
            return ordered_providers[index + 1]
        return None

    def _log_fallback(
        self,
        original_provider: str,
        reason: BaseException,
        new_provider: Optional[str],
        attempt: int,
    ) -> None:
        """Log a single fallback transition with full context."""
        if new_provider is None:
            logger.info(
                "Provider %s failed (attempt %d): %s. No more providers to try.",
                original_provider,
                attempt,
                reason,
            )
            return
        logger.info(
            "Provider %s failed (attempt %d): %s. Falling back to %s.",
            original_provider,
            attempt,
            reason,
            new_provider,
        )

    def _get_provider_name(self, model: str) -> str:
        model = model.lower()
        if "claude" in model:
            return "anthropic"
        elif "gpt" in model or "openai" in model:
            return "openai"
        else:
            return "gemini"  # Default all fallback gateway requests to Gemini

    def _error_code(self, exc: Optional[BaseException]) -> int:
        """Map a provider exception to the matching HTTP status code."""
        if isinstance(exc, ProviderRateLimitError):
            return 429
        if isinstance(exc, (ProviderTimeoutError, asyncio.TimeoutError)):
            return 408
        if isinstance(exc, ProviderAuthenticationError):
            return 401
        if isinstance(exc, ProviderConfigurationError):
            return 500
        return 500

    def _error_response(self, message: str, code: int) -> Dict[str, Any]:
        return {
            "error": {
                "message": message,
                "type": "provider_routing_error",
                "param": None,
                "code": code,
            }
        }
