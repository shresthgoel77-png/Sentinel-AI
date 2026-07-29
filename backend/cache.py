import asyncio
import logging
from collections import OrderedDict
import time
from typing import Any


logger = logging.getLogger(__name__)


class TTLInMemoryCache:
    """An async-safe TTL + LRU cache for in-process use.

    - Uses OrderedDict to track LRU order.
    - Periodically evicts expired entries in a background task.
    - Keeps the cache resilient if the cleanup loop hits an error.
    """
    def __init__(self, maxsize: int = 1024, ttl_seconds: int = 600, cleanup_interval: int = 60):
        self._store = OrderedDict()  # key -> (value, expires_at)
        self.maxsize = maxsize
        self.ttl = ttl_seconds
        self.cleanup_interval = cleanup_interval
        self._lock = asyncio.Lock()
        self._cleanup_task = None

    async def start(self):
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._run_cleanup_loop())

    async def stop(self):
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None

    async def _run_cleanup_loop(self):
        try:
            while True:
                await asyncio.sleep(self.cleanup_interval)
                await self._evict_expired()
        except asyncio.CancelledError:
            return
        except Exception as exc:  # pragma: no cover - defensive guard
            logger.exception("TTL cache cleanup loop failed: %s", exc)
            await asyncio.sleep(self.cleanup_interval)
            await self._run_cleanup_loop()

    def _evict_expired_sync(self):
        now = time.time()
        keys_to_delete = [k for k, (_, exp) in self._store.items() if exp is not None and exp <= now]
        for k in keys_to_delete:
            self._store.pop(k, None)

    async def _evict_expired(self):
        async with self._lock:
            self._evict_expired_sync()

    async def __setitem__(self, key: str, value: Any):
        expires_at = time.time() + self.ttl if self.ttl is not None else None
        async with self._lock:
            if key in self._store:
                self._store.pop(key, None)
            self._store[key] = (value, expires_at)
            while len(self._store) > self.maxsize:
                self._store.popitem(last=False)

    def __getitem__(self, key: str):
        self._evict_expired_sync()
        item = self._store.get(key)
        if item is None:
            raise KeyError(key)
        value, exp = item
        if exp is not None and exp <= time.time():
            self._store.pop(key, None)
            raise KeyError(key)
        self._store.move_to_end(key)
        return value

    def __contains__(self, key: str):
        self._evict_expired_sync()
        return key in self._store

    async def get(self, key: str, default: Any = None):
        try:
            return self.__getitem__(key)
        except KeyError:
            return default


# instantiate a global TTL cache used as in-process fallback
tasks_db = TTLInMemoryCache(maxsize=2048, ttl_seconds=600, cleanup_interval=60)
