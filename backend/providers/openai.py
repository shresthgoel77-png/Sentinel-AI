import os
from openai import AsyncOpenAI
from .base import BaseProvider

class OpenAIProvider(BaseProvider):
    async def generate_completion(self, request, api_key: str):
        # Using environment var for the upstream provider key
        client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY", "mock-openai-key"))
        
        # Pydantic v2 dump
        kwargs = request.model_dump(exclude_none=True)
        
        # Map our uniform request direct to OpenAI SDK
        response = await client.chat.completions.create(**kwargs)
        
        return response.model_dump()
