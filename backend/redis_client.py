# backend/redis_client.py
import os
import redis.asyncio as aioredis
from uuid import UUID
from dotenv import load_dotenv

load_dotenv()

# Grab the same Upstash URL you used in graph.py
REDIS_URL = os.getenv("REDIS_URL", "rediss://default:YOUR_UPSTASH_KEY@normal-dory-136084.upstash.io:6379")

class RedisStateManager:
    def __init__(self):
        self.client = aioredis.from_url(REDIS_URL, decode_responses=True)
        
    async def initialize_task(self, task_id: UUID, initial_status: str = "PARSING_COMPLETE") -> None:
        """Sets the very first status in Upstash before LangGraph starts."""
        import json
        payload = {"step": "ingestion", "message": initial_status, "is_complete": False}
        await self.client.setex(name=f"status:{str(task_id)}", time=3600, value=json.dumps(payload))

    async def close(self):
        await self.client.close()