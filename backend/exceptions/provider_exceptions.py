"""Structured exception hierarchy for provider-related failures.

All provider-specific exceptions inherit from :class:`SentinelProviderError`,
allowing callers to catch a single base type while still distinguishing
between distinct failure modes (timeout, rate limit, authentication, etc.).

Native SDK exceptions are always wrapped using ``raise ... from original``
so the original traceback and ``__cause__`` are preserved.
"""


class SentinelProviderError(Exception):
    """Base exception for all provider-related failures."""


class ProviderTimeoutError(SentinelProviderError):
    """Raised when a provider request exceeds the allowed time budget."""


class ProviderRateLimitError(SentinelProviderError):
    """Raised when a provider returns a rate-limit / 429 response."""


class ProviderAuthenticationError(SentinelProviderError):
    """Raised when a provider rejects the supplied credentials."""


class ProviderAPIError(SentinelProviderError):
    """Raised for generic provider API failures (5xx, malformed responses)."""


class ProviderConfigurationError(SentinelProviderError):
    """Raised when a provider is misconfigured (missing/invalid settings)."""


class ProviderCircuitOpenError(SentinelProviderError):
    """Raised when a request is rejected because the provider circuit is open."""
