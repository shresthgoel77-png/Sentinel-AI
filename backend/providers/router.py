import asyncio
import logging
from typing import Dict, Any

from exceptions.provider_exceptions import (
    ProviderAPIError,
    ProviderAuthenticationError,
    ProviderConfigurationError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    SentinelProviderError,
)
from .anthropic import AnthropicProvider
from .gemini import GeminiProvider
from .openai import OpenAIProvider

logger = logging.getLogger("sentinel.providers.router")


class ProviderRouter:
    def __init__(self):
        self.providers = {
            "openai": OpenAIProvider(),
            "anthropic": AnthropicProvider(),
            "gemini": GeminiProvider(),
        }

    async def route(self, request, api_key: str) -> Dict[str, Any]:
        provider_name = self._get_provider_name(request.model)
        provider = self.providers[provider_name]

        try:
            return await asyncio.wait_for(
                provider.generate_completion(request, api_key),
                timeout=30.0,
            )
        except asyncio.TimeoutError:
            logger.warning("Provider request timed out after 30s")
            return self._error_response("Provider request timed out", 408)
        except ProviderRateLimitError as exc:
            logger.warning("Provider rate limit exceeded: %s", exc)
            return self._error_response("Provider rate limit exceeded", 429)
        except ProviderAuthenticationError as exc:
            logger.warning("Provider authentication failed: %s", exc)
            return self._error_response("Provider authentication failed", 401)
        except ProviderTimeoutError as exc:
            logger.warning("Provider request timed out: %s", exc)
            return self._error_response("Provider request timed out", 408)
        except ProviderConfigurationError as exc:
            logger.error("Provider configuration error: %s", exc)
            return self._error_response("Provider configuration error", 500)
        except ProviderAPIError as exc:
            logger.error("Provider API error: %s", exc)
            return self._error_response(f"Provider error: {exc}", 500)
        except SentinelProviderError as exc:
            logger.error("Provider error: %s", exc)
            return self._error_response(f"Provider error: {exc}", 500)

    def _get_provider_name(self, model: str) -> str:
        model = model.lower()
        if "claude" in model:
            return "anthropic"
        elif "gpt" in model or "openai" in model:
            return "openai"
        else:
            return "gemini"  # Default all fallback gateway requests to Gemini

    def _error_response(self, message: str, code: int) -> Dict[str, Any]:
        return {
            "error": {
                "message": message,
                "type": "provider_routing_error",
                "param": None,
                "code": code,
            }
        }
