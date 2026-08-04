import logging

from openai import AsyncOpenAI

from exceptions.error_mapping import map_provider_error
from .base import BaseProvider

logger = logging.getLogger("sentinel.providers.openai")


class OpenAIProvider(BaseProvider):
    async def generate_completion(self, request, api_key: str):
        client = AsyncOpenAI(api_key=api_key)

        # Pydantic v2 dump
        kwargs = request.model_dump(exclude_none=True)

        try:
            # Map our uniform request direct to OpenAI SDK
            response = await client.chat.completions.create(**kwargs)
        except Exception as exc:
            logger.warning("OpenAI provider request failed: %s", exc)
            # map_provider_error always raises the mapped Sentinel exception,
            # chained to the original via `raise ... from original`.
            map_provider_error(exc)

        return response.model_dump()
