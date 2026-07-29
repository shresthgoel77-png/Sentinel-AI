import asyncio
import time

from cache import TTLInMemoryCache


def test_cache_eviction_removes_expired_entries():
    cache = TTLInMemoryCache(maxsize=8, ttl_seconds=0.05, cleanup_interval=0.01)

    async def run_test():
        await cache.start()
        try:
            await cache.__setitem__("task-1", {"status": "processing"})
            assert "task-1" in cache
            assert cache["task-1"]["status"] == "processing"

            await asyncio.sleep(0.08)
            await cache._evict_expired()

            assert "task-1" not in cache
            assert await cache.get("task-1") is None
        finally:
            await cache.stop()

    asyncio.run(run_test())
