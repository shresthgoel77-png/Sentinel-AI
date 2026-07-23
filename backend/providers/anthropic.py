import os
from anthropic import AsyncAnthropic, NotGiven
from .base import BaseProvider

#anthropic 
# provider 
class AnthropicProvider(BaseProvider):
    async def generate_completion(self, request, api_key: str):
        client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY", "mock-anthropic-key"))

        system_messages = [m.content for m in request.messages if m.role == "system"]
        anthropic_messages = [{"role": m.role, "content": m.content} for m in request.messages if m.role != "system"]
        
        system_prompt = system_messages[0] if system_messages else NotGiven()
        
        kwargs = {
            "model": request.model,
            "max_tokens": request.max_tokens or 1024,
            "messages": anthropic_messages,
        }
        
        if system_prompt is not NotGiven():
            kwargs["system"] = system_prompt
        if request.temperature is not None:
            kwargs["temperature"] = request.temperature
            
        response = await client.messages.create(**kwargs)
        
        # Map Anthropic output back to OpenAI uniform JSON wrapper
        return {
            "id": response.id,
            "object": "chat.completion",
            "created": 1677652288,
            "model": response.model,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": response.content[0].text if response.content else ""
                },
                "finish_reason": "stop"
            }],

            "usage": {
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens
            }
        }
        
        
