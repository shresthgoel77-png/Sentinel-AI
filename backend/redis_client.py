import os
import json
from uuid import UUID
import redis.asyncio as redis
from dotenv import load_dotenv

# Load variables from .env
load_dotenv()

class RedisManager:
    def __init__(self):
        # 1. Grab the URL from the environment
        redis_url = os.getenv("REDIS_URL")
        
        if not redis_url:
            raise ValueError("REDIS_URL environment variable is missing. Please set it in your environment or .env file.")

        # 2. Create the async Redis client 
        # (Removed the explicit ssl=True because 'rediss://' handles it automatically)
        self.client = redis.from_url(
            url=redis_url.strip(),
            encoding="utf-8",
            decode_responses=True,
        )

    async def initialize_task(
        self,
        task_id: UUID,
        initial_status: str = "PARSING_COMPLETE",
    ) -> None:
        """Sets the very first status in Upstash before LangGraph starts."""
        payload = {
            "step": "ingestion",
            "message": initial_status,
            "is_complete": False,
        }

        await self.client.setex(
            name=f"status:{task_id}",
            time=3600,
            value=json.dumps(payload),
        )

    async def close(self):
        await self.client.close()