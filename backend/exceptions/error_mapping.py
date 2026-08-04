"""Reusable helpers that map native provider SDK exceptions to Sentinel exceptions.

These functions centralize the mapping logic so each provider implementation
does not duplicate the same ``except`` blocks.  Native exceptions are always
preserved via ``raise ... from original`` so ``__cause__`` and the original
traceback remain intact.
"""

from __future__ import annotations

from typing import Optional, Type, TypeVar

from .provider_exceptions import (
    ProviderAPIError,
    ProviderAuthenticationError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    SentinelProviderError,
)

# ---------------------------------------------------------------------------
# Defensive SDK imports
#
# Not every environment has every provider SDK installed.  We import lazily
# and fall back to a sentinel class that never matches, so the mapping helpers
# remain importable even when a particular SDK is absent.
# ---------------------------------------------------------------------------


class _UnavailableSDKError(Exception):
    """Sentinel class used when a provider SDK is not installed.

    Because no real exception is ever an instance of this class, ``isinstance``
    checks against it always return ``False``.  This prevents the mapping
    helpers from accidentally matching *every* exception when an SDK is absent.
    """


try:  # pragma: no cover - depends on environment
    from openai import (
        APIConnectionError as _OpenAIAPIConnectionError,
        APIError as _OpenAIAPIError,
        APITimeoutError as _OpenAIAPITimeoutError,
        AuthenticationError as _OpenAIAuthenticationError,
        RateLimitError as _OpenAIRateLimitError,
    )
except ImportError:  # pragma: no cover - depends on environment
    _OpenAIAPIConnectionError = _UnavailableSDKError
    _OpenAIAPIError = _UnavailableSDKError
    _OpenAIAPITimeoutError = _UnavailableSDKError
    _OpenAIAuthenticationError = _UnavailableSDKError
    _OpenAIRateLimitError = _UnavailableSDKError

try:  # pragma: no cover - depends on environment
    from anthropic import (
        APIConnectionError as _AnthropicAPIConnectionError,
        APIError as _AnthropicAPIError,
        APITimeoutError as _AnthropicAPITimeoutError,
        AuthenticationError as _AnthropicAuthenticationError,
        RateLimitError as _AnthropicRateLimitError,
    )
except ImportError:  # pragma: no cover - depends on environment
    _AnthropicAPIConnectionError = _UnavailableSDKError
    _AnthropicAPIError = _UnavailableSDKError
    _AnthropicAPITimeoutError = _UnavailableSDKError
    _AnthropicAuthenticationError = _UnavailableSDKError
    _AnthropicRateLimitError = _UnavailableSDKError

try:  # pragma: no cover - depends on environment
    from google.genai import errors as _GenAIErrors
except ImportError:  # pragma: no cover - depends on environment
    _GenAIErrors = None  # type: ignore[assignment]

_T = TypeVar("_T", bound=SentinelProviderError)


def _raise_mapped(
    exc_type: Type[_T],
    message: str,
    original: BaseException,
) -> None:
    """Raise ``exc_type`` chained to ``original``.

    Using ``raise ... from original`` preserves the original traceback and
    sets ``__cause__`` on the new exception.
    """
    raise exc_type(message) from original


def map_openai_error(exc: BaseException) -> None:
    """Map an OpenAI SDK exception to the matching Sentinel exception.

    Raises the mapped Sentinel exception chained to ``exc``.  If the
    exception is not recognised, it is re-raised unchanged.
    """
    if isinstance(exc, _OpenAIAuthenticationError):
        _raise_mapped(
            ProviderAuthenticationError,
            f"OpenAI authentication failed: {exc}",
            exc,
        )
    if isinstance(exc, _OpenAIRateLimitError):
        _raise_mapped(
            ProviderRateLimitError,
            f"OpenAI rate limit exceeded: {exc}",
            exc,
        )
    if isinstance(exc, _OpenAIAPITimeoutError):
        _raise_mapped(
            ProviderTimeoutError,
            f"OpenAI request timed out: {exc}",
            exc,
        )
    if isinstance(exc, _OpenAIAPIConnectionError):
        _raise_mapped(
            ProviderTimeoutError,
            f"OpenAI connection error: {exc}",
            exc,
        )
    if isinstance(exc, _OpenAIAPIError):
        _raise_mapped(
            ProviderAPIError,
            f"OpenAI API error: {exc}",
            exc,
        )


def map_anthropic_error(exc: BaseException) -> None:
    """Map an Anthropic SDK exception to the matching Sentinel exception.

    Raises the mapped Sentinel exception chained to ``exc``.  If the
    exception is not recognised, it is re-raised unchanged.
    """
    if isinstance(exc, _AnthropicAuthenticationError):
        _raise_mapped(
            ProviderAuthenticationError,
            f"Anthropic authentication failed: {exc}",
            exc,
        )
    if isinstance(exc, _AnthropicRateLimitError):
        _raise_mapped(
            ProviderRateLimitError,
            f"Anthropic rate limit exceeded: {exc}",
            exc,
        )
    if isinstance(exc, _AnthropicAPITimeoutError):
        _raise_mapped(
            ProviderTimeoutError,
            f"Anthropic request timed out: {exc}",
            exc,
        )
    if isinstance(exc, _AnthropicAPIConnectionError):
        _raise_mapped(
            ProviderTimeoutError,
            f"Anthropic connection error: {exc}",
            exc,
        )
    if isinstance(exc, _AnthropicAPIError):
        _raise_mapped(
            ProviderAPIError,
            f"Anthropic API error: {exc}",
            exc,
        )


def _genai_status_code(exc: BaseException) -> Optional[int]:
    """Best-effort extraction of the HTTP status code from a GenAI error."""
    code = getattr(exc, "code", None)
    if isinstance(code, int):
        return code
    status = getattr(exc, "status", None)
    if isinstance(status, int):
        return status
    return None


def map_genai_error(exc: BaseException) -> None:
    """Map a Google GenAI SDK exception to the matching Sentinel exception.

    The GenAI SDK exposes a single ``errors.APIError`` with ``code``,
    ``status`` and ``message`` attributes.  We map based on the HTTP status
    code when available, otherwise fall back to ``ProviderAPIError``.

    Raises the mapped Sentinel exception chained to ``exc``.  If the
    exception is not recognised, it is re-raised unchanged.
    """
    if _GenAIErrors is not None and isinstance(exc, _GenAIErrors.APIError):
        code = _genai_status_code(exc)
        if code == 401 or code == 403:
            _raise_mapped(
                ProviderAuthenticationError,
                f"Gemini authentication failed: {exc}",
                exc,
            )
        if code == 429:
            _raise_mapped(
                ProviderRateLimitError,
                f"Gemini rate limit exceeded: {exc}",
                exc,
            )
        if code == 408 or code == 504:
            _raise_mapped(
                ProviderTimeoutError,
                f"Gemini request timed out: {exc}",
                exc,
            )
        _raise_mapped(
            ProviderAPIError,
            f"Gemini API error: {exc}",
            exc,
        )


def map_provider_error(exc: BaseException) -> None:
    """Dispatch a native provider exception to the correct mapper.

    This is the single entry point used by provider implementations.  It
    tries each known SDK mapper in turn; if none match, the original
    exception is re-raised unchanged.
    """
    map_openai_error(exc)
    map_anthropic_error(exc)
    map_genai_error(exc)
    raise exc
