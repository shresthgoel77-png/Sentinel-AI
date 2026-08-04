# pyrefly: ignore [missing-import]
"""Unit tests for the structured provider exception hierarchy and error mapping."""

import sys
import os

import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from exceptions.provider_exceptions import (
    SentinelProviderError,
    ProviderTimeoutError,
    ProviderRateLimitError,
    ProviderAuthenticationError,
    ProviderAPIError,
    ProviderConfigurationError,
)
from exceptions.error_mapping import (
    map_openai_error,
    map_anthropic_error,
    map_genai_error,
    map_provider_error,
)

# ---------------------------------------------------------------------------
# Exception hierarchy
# ---------------------------------------------------------------------------


class TestExceptionHierarchy:
    def test_all_exceptions_inherit_from_base(self):
        """Every provider-specific exception must inherit from SentinelProviderError."""
        assert issubclass(ProviderTimeoutError, SentinelProviderError)
        assert issubclass(ProviderRateLimitError, SentinelProviderError)
        assert issubclass(ProviderAuthenticationError, SentinelProviderError)
        assert issubclass(ProviderAPIError, SentinelProviderError)
        assert issubclass(ProviderConfigurationError, SentinelProviderError)

    def test_base_exception_is_catchable(self):
        """Catching SentinelProviderError catches all subclasses."""
        with pytest.raises(SentinelProviderError):
            raise ProviderTimeoutError("timeout")

    def test_exceptions_are_instances_of_base(self):
        """Instances of subclasses are also instances of the base."""
        assert isinstance(ProviderRateLimitError("x"), SentinelProviderError)
        assert isinstance(ProviderAuthenticationError("x"), SentinelProviderError)
        assert isinstance(ProviderAPIError("x"), SentinelProviderError)
        assert isinstance(ProviderConfigurationError("x"), SentinelProviderError)


# ---------------------------------------------------------------------------
# OpenAI error mapping
# ---------------------------------------------------------------------------


class TestOpenAIErrorMapping:
    def _make_openai_error(self, exc_cls, message="boom"):
        """Construct an OpenAI SDK error with a minimal httpx response."""
        import httpx
        from openai import APIConnectionError, APIError, APITimeoutError

        request = httpx.Request("POST", "http://test")

        # APIConnectionError and APITimeoutError use a different constructor.
        if exc_cls in (APIConnectionError, APITimeoutError):
            return exc_cls(request=request)

        # Base APIError uses (message, request, *, body).
        if exc_cls is APIError:
            return exc_cls(message, request=request, body=None)

        response = httpx.Response(500, request=request)
        return exc_cls(message, response=response, body=None)

    def test_authentication_error_maps(self):
        from openai import AuthenticationError

        original = self._make_openai_error(AuthenticationError, "bad key")
        with pytest.raises(ProviderAuthenticationError) as exc_info:
            map_openai_error(original)
        assert exc_info.value.__cause__ is original
        assert "authentication" in str(exc_info.value).lower()

    def test_rate_limit_error_maps(self):
        from openai import RateLimitError

        original = self._make_openai_error(RateLimitError, "too many")
        with pytest.raises(ProviderRateLimitError) as exc_info:
            map_openai_error(original)
        assert exc_info.value.__cause__ is original
        assert "rate limit" in str(exc_info.value).lower()

    def test_timeout_error_maps(self):
        from openai import APITimeoutError

        original = self._make_openai_error(APITimeoutError, "slow")
        with pytest.raises(ProviderTimeoutError) as exc_info:
            map_openai_error(original)
        assert exc_info.value.__cause__ is original
        assert "timed out" in str(exc_info.value).lower()

    def test_connection_error_maps_to_timeout(self):
        from openai import APIConnectionError

        original = self._make_openai_error(APIConnectionError, "conn refused")
        with pytest.raises(ProviderTimeoutError) as exc_info:
            map_openai_error(original)
        assert exc_info.value.__cause__ is original

    def test_generic_api_error_maps(self):
        from openai import APIError

        original = self._make_openai_error(APIError, "server 500")
        with pytest.raises(ProviderAPIError) as exc_info:
            map_openai_error(original)
        assert exc_info.value.__cause__ is original
        assert "api error" in str(exc_info.value).lower()

    def test_unknown_error_is_reraisable(self):
        """An unrecognised exception is re-raised unchanged by map_provider_error."""
        original = ValueError("not an SDK error")
        with pytest.raises(ValueError) as exc_info:
            map_provider_error(original)
        assert exc_info.value is original


# ---------------------------------------------------------------------------
# Anthropic error mapping
# ---------------------------------------------------------------------------


class TestAnthropicErrorMapping:
    def test_authentication_error_maps(self):
        """Anthropic AuthenticationError maps to ProviderAuthenticationError."""

        # Build a fake anthropic-style error class since the SDK may not be installed.
        class FakeAnthropicAuthError(Exception):
            pass

        original = FakeAnthropicAuthError("bad key")
        # Patch the module-level _AnthropicAuthenticationError to our fake.
        import exceptions.error_mapping as em

        old = em._AnthropicAuthenticationError
        em._AnthropicAuthenticationError = FakeAnthropicAuthError
        try:
            with pytest.raises(ProviderAuthenticationError) as exc_info:
                map_anthropic_error(original)
            assert exc_info.value.__cause__ is original
        finally:
            em._AnthropicAuthenticationError = old

    def test_rate_limit_error_maps(self):
        class FakeAnthropicRateLimitError(Exception):
            pass

        original = FakeAnthropicRateLimitError("rate limited")
        import exceptions.error_mapping as em

        old = em._AnthropicRateLimitError
        em._AnthropicRateLimitError = FakeAnthropicRateLimitError
        try:
            with pytest.raises(ProviderRateLimitError) as exc_info:
                map_anthropic_error(original)
            assert exc_info.value.__cause__ is original
        finally:
            em._AnthropicRateLimitError = old

    def test_timeout_error_maps(self):
        class FakeAnthropicTimeoutError(Exception):
            pass

        original = FakeAnthropicTimeoutError("timed out")
        import exceptions.error_mapping as em

        old = em._AnthropicAPITimeoutError
        em._AnthropicAPITimeoutError = FakeAnthropicTimeoutError
        try:
            with pytest.raises(ProviderTimeoutError) as exc_info:
                map_anthropic_error(original)
            assert exc_info.value.__cause__ is original
        finally:
            em._AnthropicAPITimeoutError = old

    def test_connection_error_maps_to_timeout(self):
        class FakeAnthropicConnError(Exception):
            pass

        original = FakeAnthropicConnError("conn refused")
        import exceptions.error_mapping as em

        old = em._AnthropicAPIConnectionError
        em._AnthropicAPIConnectionError = FakeAnthropicConnError
        try:
            with pytest.raises(ProviderTimeoutError) as exc_info:
                map_anthropic_error(original)
            assert exc_info.value.__cause__ is original
        finally:
            em._AnthropicAPIConnectionError = old

    def test_generic_api_error_maps(self):
        class FakeAnthropicAPIError(Exception):
            pass

        original = FakeAnthropicAPIError("server error")
        import exceptions.error_mapping as em

        old = em._AnthropicAPIError
        em._AnthropicAPIError = FakeAnthropicAPIError
        try:
            with pytest.raises(ProviderAPIError) as exc_info:
                map_anthropic_error(original)
            assert exc_info.value.__cause__ is original
        finally:
            em._AnthropicAPIError = old


# ---------------------------------------------------------------------------
# Google GenAI error mapping
# ---------------------------------------------------------------------------


class TestGenAIErrorMapping:
    def _make_genai_error(self, code, message="genai error"):
        """Build a fake GenAI-style APIError with code/status/message attributes."""
        import exceptions.error_mapping as em

        class FakeGenAIError(Exception):
            def __init__(self, code, message):
                self.code = code
                self.status = None
                self.message = message
                super().__init__(message)

        # Patch the module-level _GenAIErrors to expose our fake APIError.
        old = em._GenAIErrors

        class FakeGenAIErrors:
            APIError = FakeGenAIError

        em._GenAIErrors = FakeGenAIErrors
        return FakeGenAIError(code, message), old

    def test_authentication_error_maps(self):
        import exceptions.error_mapping as em

        original, old = self._make_genai_error(401, "unauthorized")
        try:
            with pytest.raises(ProviderAuthenticationError) as exc_info:
                map_genai_error(original)
            assert exc_info.value.__cause__ is original
        finally:
            em._GenAIErrors = old

    def test_forbidden_error_maps_to_authentication(self):
        import exceptions.error_mapping as em

        original, old = self._make_genai_error(403, "forbidden")
        try:
            with pytest.raises(ProviderAuthenticationError) as exc_info:
                map_genai_error(original)
            assert exc_info.value.__cause__ is original
        finally:
            em._GenAIErrors = old

    def test_rate_limit_error_maps(self):
        import exceptions.error_mapping as em

        original, old = self._make_genai_error(429, "rate limited")
        try:
            with pytest.raises(ProviderRateLimitError) as exc_info:
                map_genai_error(original)
            assert exc_info.value.__cause__ is original
        finally:
            em._GenAIErrors = old

    def test_timeout_error_maps(self):
        import exceptions.error_mapping as em

        original, old = self._make_genai_error(408, "timeout")
        try:
            with pytest.raises(ProviderTimeoutError) as exc_info:
                map_genai_error(original)
            assert exc_info.value.__cause__ is original
        finally:
            em._GenAIErrors = old

    def test_gateway_timeout_maps(self):
        import exceptions.error_mapping as em

        original, old = self._make_genai_error(504, "gateway timeout")
        try:
            with pytest.raises(ProviderTimeoutError) as exc_info:
                map_genai_error(original)
            assert exc_info.value.__cause__ is original
        finally:
            em._GenAIErrors = old

    def test_generic_api_error_maps(self):
        import exceptions.error_mapping as em

        original, old = self._make_genai_error(500, "server error")
        try:
            with pytest.raises(ProviderAPIError) as exc_info:
                map_genai_error(original)
            assert exc_info.value.__cause__ is original
        finally:
            em._GenAIErrors = old


# ---------------------------------------------------------------------------
# Traceback chaining
# ---------------------------------------------------------------------------


class TestTracebackChaining:
    def test_cause_is_preserved(self):
        """The original exception is preserved via __cause__."""
        original = RuntimeError("original failure")
        try:
            try:
                raise original
            except RuntimeError:
                raise ProviderAPIError("wrapped") from original
        except ProviderAPIError as exc:
            assert exc.__cause__ is original

    def test_traceback_chain_works(self):
        """The full traceback chain is accessible."""
        original = ValueError("root cause")
        try:
            try:
                raise original
            except ValueError:
                raise ProviderTimeoutError("timeout") from original
        except ProviderTimeoutError as exc:
            # __cause__ points to the original
            assert exc.__cause__ is original
            # __context__ is also set (implicit chaining)
            assert exc.__context__ is original
