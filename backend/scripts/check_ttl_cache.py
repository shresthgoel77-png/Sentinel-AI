import asyncio
import time
from cache import TTLInMemoryCache


async def run():
    cache = TTLInMemoryCache(maxsize=3, ttl_seconds=2, cleanup_interval=1)
    await cache.start()
    print('Started cache (ttl=2s, cleanup=1s, maxsize=3)')

    await cache.__setitem__('k1', {'val': 1})
    await cache.__setitem__('k2', {'val': 2})
    print('Inserted k1, k2')

    v = await cache.get('k1')
    print('get k1 ->', v)

    print('Sleeping 3s to allow TTL to expire...')
    await asyncio.sleep(3)

    v2 = await cache.get('k1')
    print('after sleep get k1 ->', v2)

    await cache.stop()
    print('Stopped cache')

if __name__ == '__main__':
    asyncio.run(run())
