import time
import logging
import os

from google import genai

from exceptions.error_mapping import map_provider_error
from .base import BaseProvider

logger = logging.getLogger("sentinel.providers.gemini")


class GeminiProvider(BaseProvider):
    async def generate_completion(self, request, api_key: str):
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY", "mock-gemini-key"))

        gemini_messages = []
        for m in request.messages:
            if m.role == "system":
                continue
            role = "model" if m.role == "assistant" else "user"
            gemini_messages.append({"role": role, "parts": [{"text": m.content}]})

        system_instruction = [m.content for m in request.messages if m.role == "system"]

        config = {}
        if getattr(request, "temperature", None) is not None:
            config["temperature"] = request.temperature
        if getattr(request, "max_tokens", None) is not None:
            config["max_output_tokens"] = request.max_tokens

        if system_instruction:
            config["system_instruction"] = system_instruction[0]

        kwargs = {
            "model": request.model,
            "contents": gemini_messages,
        }
        if config:
            kwargs["config"] = config

        try:
            response = await client.aio.models.generate_content(**kwargs)
        except Exception as exc:
            logger.warning("Gemini provider request failed: %s", exc)
            # map_provider_error always raises the mapped Sentinel exception,
            # chained to the original via `raise ... from original`.
            map_provider_error(exc)

        return {
            "id": f"gemini-{int(time.time())}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": request.model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response.text,
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": (
                    response.usage_metadata.prompt_token_count
                    if response.usage_metadata
                    else 0
                ),
                "completion_tokens": (
                    response.usage_metadata.candidates_token_count
                    if response.usage_metadata
                    else 0
                ),
                "total_tokens": (
                    response.usage_metadata.total_token_count
                    if response.usage_metadata
                    else 0
                ),
            },
        }
