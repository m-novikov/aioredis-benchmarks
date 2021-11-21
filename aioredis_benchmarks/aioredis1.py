"""
Taken from github issue https://github.com/aio-libs/aioredis-py/issues/1208
Author: https://github.com/artesby
"""
import asyncio
import os
import time
import aioredis
from . import bench_config

url = bench_config.url
max_conn = bench_config.max_conn
num_iterations = bench_config.num_iterations

async def task(i, redis):
    key = f'key:{i}'
    v = await redis.get(key)
    new_v = 1 if v is None else int(v) + 1
    await redis.set(key, new_v, expire=600)

async def run(n=1500):
    redis = await aioredis.create_redis_pool(
        url, encoding='utf-8', maxsize=max_conn
    )

    tasks = [asyncio.create_task(task(i, redis)) for i in range(n)]
    start = time.time()
    await asyncio.gather(*tasks)
    t = time.time() - start
    print(f'aioredis1: {n} tasks with blocking pool with {max_conn} connections: {t}s')


if __name__ == "__main__":
    asyncio.run(run(n=bench_config.num_iterations))
