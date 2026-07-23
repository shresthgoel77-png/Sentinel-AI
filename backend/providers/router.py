import asyncio
from typing import Dict, Any
from .openai import OpenAIProvider
from .anthropic import AnthropicProvider
from .gemini import GeminiProvider

class ProviderRouter:
    def __init__(self):
        self.providers = {
            "openai": OpenAIProvider(),
            "anthropic": AnthropicProvider(),
            "gemini": GeminiProvider()
        }

    async def route(self, request, api_key: str) -> Dict[str, Any]:
        provider_name = self._get_provider_name(request.model)
        provider = self.providers[provider_name]
        
        try:
            return await asyncio.wait_for(
                provider.generate_completion(request, api_key), 
                timeout=30.0
            )
        except asyncio.TimeoutError:
            return self._error_response("Provider request timed out", 408)
        except Exception as e:
            error_str = str(e).lower()
            if "rate limit" in error_str or "429" in error_str:
                return self._error_response("Provider rate limit exceeded", 429)
            return self._error_response(f"Provider error: {str(e)}", 500)

    def _get_provider_name(self, model: str) -> str:
        model = model.lower()
        if "claude" in model:
            return "anthropic"
        elif "gemini" in model:
            return "gemini"
        else:
            return "openai"

    def _error_response(self, message: str, code: int) -> Dict[str, Any]:
        return {
            "error": {
                "message": message,
                "type": "provider_routing_error",
                "param": None,
                "code": code
            }
        }
